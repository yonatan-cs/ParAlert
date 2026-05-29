"""
ParAlert Backend — the connecting brain. OWNER: Dev 2.

Flow:
  Simulator --POST /ingest--> [analyze] --if toxic--> [recommend] --> save Alert
  Frontend  --GET  /alerts--> list of Alerts (contract C)

ML (Dev 1) and recommendation engine (Dev 4) are imported as black boxes.
Both calls are wrapped so a failure degrades gracefully instead of crashing the demo.

Run:  uvicorn main:app --port 8000   (Swagger at /docs)
      On Windows, avoid --reload: WatchFiles can stall and keep serving stale code.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import (  # noqa: E402
    Alert, AnalysisResult, AnalyzeResponse, ChatBubble, IncomingMessage,
    MediaReport, escalation_from, severity_from_score,
)
from backend_api import database  # noqa: E402

# Tunable at runtime via env vars — no code edit needed to flip the model on stage.
#   USE_MODEL=true   -> load the real HF model (keyword fallback if it fails to load)
#   ALERT_THRESHOLD  -> min toxicity score to raise an alert (0.5 matches severity_from_score)
USE_MODEL = os.getenv("USE_MODEL", "false").lower() == "true"
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.5"))
# Below this credibility score, a non-bullying message is raised as a disinformation alert.
# fact_check runs with has_media=False so a plain photo is never auto-flagged as "fake".
DISINFO_THRESHOLD = float(os.getenv("DISINFO_THRESHOLD", "0.5"))
# Seconds of socket idle before the server sends a heartbeat ping (keeps proxies open).
WS_HEARTBEAT_SECONDS = float(os.getenv("WS_HEARTBEAT_SECONDS", "25"))
# When set (e.g. a Cloudflare Tunnel URL to a powerful local box), heavy ML runs THERE instead of
# in-process — Render stays light (no torch) while judges still get real-model scores.
# Routing is active only when USE_MODEL=true AND this is set; any failure falls back to
# the in-process keyword analyzer so the endpoint never hard-fails.
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "").strip().rstrip("/")
ML_TIMEOUT = float(os.getenv("ML_TIMEOUT", "30"))
# Comma-separated allowed origins for the deployed frontend; "*" is fine for the demo.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
_MOCK_ALERTS_PATH = os.path.join(os.path.dirname(__file__), "..", "contracts", "mock_alerts.json")

# ---- black-box deps (graceful import: demo runs even if a teammate's module is missing) ----
# Load a real model in-process only if asked AND not routing to a remote ML service
# (Render can't hold torch in 512MB; remote routing keeps the in-process side light).
_LOCAL_USE_MODEL = USE_MODEL and not ML_SERVICE_URL
try:
    from ml_service.analyzer import ToxicityAnalyzer
    _analyzer = ToxicityAnalyzer(use_model=_LOCAL_USE_MODEL)
except Exception as exc:  # noqa: BLE001
    print(f"[backend] analyzer unavailable, using stub: {exc}")
    _analyzer = None

try:
    from simulator_and_logic.recommendation_engine import generate_recommendation
except Exception as exc:  # noqa: BLE001
    print(f"[backend] recommendation engine unavailable, using stub: {exc}")
    generate_recommendation = None

try:
    from simulator_and_logic.fact_check import check_claim
except Exception as exc:  # noqa: BLE001
    print(f"[backend] fact_check unavailable, disinformation alerts skip credibility: {exc}")
    check_claim = None

app = FastAPI(title="ParAlert API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"]
)


# Connected dashboards for real-time alert push. Polling /alerts still works in parallel.
_ws_clients: set[WebSocket] = set()
_ws_locks: dict[WebSocket, asyncio.Lock] = {}  # serialize sends per socket (no frame interleave)
_loop: asyncio.AbstractEventLoop | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _loop
    database.init_db()
    _loop = asyncio.get_running_loop()  # captured so the sync /ingest can broadcast onto it
    # Render free tier wipes the ephemeral SQLite on every restart/redeploy, so we
    # auto-reload the demo dataset whenever the DB is empty (default ON; set
    # SEED_ON_STARTUP=false to disable). Defaulting on keeps the dashboard populated
    # for judges even if the env var never reached the service (blueprint not synced).
    if os.getenv("SEED_ON_STARTUP", "true").lower() == "true" and not database.get_alerts():
        seeded = _seed_from_mock()
        print(f"[backend] DB empty on startup, auto-seeded {seeded} demo alerts")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "analyzer": getattr(_analyzer, "model_name", "stub"),
        "use_model": USE_MODEL,
        "alert_threshold": ALERT_THRESHOLD,
        "ml_service": ML_SERVICE_URL or None,
        "ml_routing": bool(ML_SERVICE_URL and USE_MODEL),
    }


@app.post("/ingest")
def ingest(message: IncomingMessage) -> dict[str, object]:
    """Analyze one chat message and raise a bullying or disinformation alert."""
    analysis = _analyze(message)
    if analysis.is_toxic and analysis.toxicity_score >= ALERT_THRESHOLD:
        return _save_and_push(_build_alert(message, analysis))

    # Not bullying — check the text for disinformation (low credibility). This is the
    # live counterpart to the seeded disinfo demo data, gated so benign chatter is ignored.
    disinfo = _disinfo_analysis(message)
    if disinfo is not None:
        return _save_and_push(_build_alert(message, disinfo))

    return {"alert_created": False, "toxicity_score": analysis.toxicity_score}


def _save_and_push(alert: Alert) -> dict[str, object]:
    """Persist an alert (contract C) and push it to connected dashboards."""
    payload = alert.model_dump(mode="json")
    database.save_alert(payload)
    _broadcast(payload)
    return {"alert_created": True, "alert_id": alert.alert_id, "alert_type": alert.alert_type}


@app.get("/alerts")
def list_alerts(child_id: str | None = None) -> list[dict]:
    """Feed for the parent dashboard (contract C)."""
    return database.get_alerts(child_id)


@app.post("/demo/seed")
def demo_seed() -> dict[str, object]:
    """Reset to a clean demo set (contracts/mock_alerts.json). Idempotent; re-runnable."""
    return {"seeded": _seed_from_mock()}


# ---- interactive "Try it" analysis (judge playground) ----
class AnalyzeRequest(BaseModel):
    text: str = ""
    media_url: str | None = None


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze submitted text (+ optional media URL) and return a full report. A
    toxic/disinformation submission also pops as a live alert on the dashboard."""
    message = _playground_message(req.text, req.media_url, _media_type_of(req.media_url))
    resp = _full_report(message)
    _maybe_alert(message, resp)
    return resp


@app.post("/analyze/upload", response_model=AnalyzeResponse)
async def analyze_upload(text: str = Form(""), file: UploadFile | None = File(None)) -> AnalyzeResponse:
    """Same as /analyze but for an uploaded image/video file."""
    media_type, tmp_path = None, None
    if file is not None and file.filename:
        suffix = os.path.splitext(file.filename)[1].lower() or ".bin"
        media_type = "video" if suffix in {".mp4", ".mov", ".avi", ".mkv", ".webm"} else "image"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as out:
            out.write(await file.read())
    try:
        message = _playground_message(text, None, media_type)
        # Offload the (possibly blocking) analysis off the event loop.
        resp = await asyncio.to_thread(_full_report, message, tmp_path, media_type)
        await asyncio.to_thread(_maybe_alert, message, resp)
        return resp
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _playground_message(text, media_url, media_type) -> IncomingMessage:
    return IncomingMessage(
        message_id=f"try_{uuid.uuid4().hex[:8]}",
        group_name="🧪 Try it", sender_id="judge", sender_name="Judge", child_id="judge",
        text=text or "", media_url=media_url or None, media_type=media_type or None,
        timestamp=datetime.now(),
    )


def _full_report(message: IncomingMessage, upload_path: str | None = None,
                 upload_media_type: str | None = None) -> AnalyzeResponse:
    """Toxicity + media (remote ML service if configured, else in-process keyword),
    then disinformation/credibility (always backend-side). Never raises."""
    resp = None
    if ML_SERVICE_URL and USE_MODEL:
        resp = _remote_report(message, upload_path)
    if resp is None:  # not configured, or remote failed -> graceful local fallback
        resp = _local_report(message, upload_path, upload_media_type)
    _add_disinfo(message, resp)
    return resp


def _local_report(message, upload_path, upload_media_type) -> AnalyzeResponse:
    if _analyzer is None:
        return AnalyzeResponse(is_toxic=False, toxicity_score=0.0, category="none",
                               role_of_child="none", explanation="analyzer stub", model_used="stub")
    text_result = _analyzer.analyze(message)
    media = _local_media(message, upload_path, upload_media_type)
    is_toxic = text_result.is_toxic or (media is not None and media.is_harmful)
    score = max(text_result.toxicity_score, media.safety_score if media else 0.0)
    category = text_result.category
    if media is not None and media.is_harmful and media.safety_score >= text_result.toxicity_score:
        category = "sexual"
    return AnalyzeResponse(
        is_toxic=is_toxic, toxicity_score=round(score, 3),
        category=category if is_toxic else "none", role_of_child=text_result.role_of_child,
        alert_type=text_result.alert_type, explanation=text_result.explanation,
        model_used=text_result.model_used, media=media,
    )


def _local_media(message, upload_path, upload_media_type) -> MediaReport | None:
    vision = getattr(_analyzer, "vision", None)
    if vision is None:
        return None
    try:
        if upload_path:
            m = vision.analyze_path(Path(upload_path))
            mt = upload_media_type
        elif message.media_url:
            m = vision.analyze_url(message.media_url)
            mt = message.media_type or _media_type_of(message.media_url)
        else:
            return None
        return MediaReport(media_type=mt, safety_score=m.safety_score, ai_score=m.ai_score,
                           is_harmful=m.is_harmful, model_used=m.model_used, explanation=m.explanation)
    except Exception as exc:  # noqa: BLE001
        print(f"[backend] media analysis failed: {exc}")
        return None


def _remote_report(message: IncomingMessage, upload_path: str | None) -> AnalyzeResponse | None:
    """Call the remote ML service (real models). Returns None on any failure."""
    try:
        import requests  # local import: optional dep
        if upload_path:
            with open(upload_path, "rb") as fh:
                files = {"file": (f"upload{os.path.splitext(upload_path)[1]}", fh)}
                r = requests.post(f"{ML_SERVICE_URL}/analyze/upload",
                                  data={"text": message.text}, files=files, timeout=ML_TIMEOUT)
        else:
            r = requests.post(f"{ML_SERVICE_URL}/analyze",
                              json={"text": message.text, "media_url": message.media_url},
                              timeout=ML_TIMEOUT)
        r.raise_for_status()
        return AnalyzeResponse(**r.json())
    except Exception as exc:  # noqa: BLE001
        print(f"[backend] remote ML service failed, keyword fallback: {exc}")
        return None


def _add_disinfo(message: IncomingMessage, resp: AnalyzeResponse) -> None:
    """If not toxic, fact-check the text; low credibility -> disinformation report."""
    if resp.is_toxic or check_claim is None or not (message.text or "").strip():
        return
    try:
        cred = check_claim(message.text, has_media=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[backend] disinfo fact_check failed: {exc}")
        return
    if cred is None or cred.score >= DISINFO_THRESHOLD:
        return
    resp.alert_type = "disinformation"
    resp.category = "disinformation"
    resp.role_of_child = "exposed"
    resp.credibility = cred
    resp.toxicity_score = max(resp.toxicity_score, round(1.0 - cred.score, 3))


def _maybe_alert(message: IncomingMessage, resp: AnalyzeResponse) -> None:
    """Pop a live dashboard alert for a toxic/disinformation submission."""
    is_disinfo = resp.alert_type == "disinformation" and resp.credibility is not None
    is_bully = resp.is_toxic and resp.toxicity_score >= ALERT_THRESHOLD
    if not (is_bully or is_disinfo):
        return
    analysis = AnalysisResult(
        message_id=message.message_id, is_toxic=is_bully, toxicity_score=resp.toxicity_score,
        category=resp.category, role_of_child=resp.role_of_child, explanation=resp.explanation,
        model_used=resp.model_used, alert_type=resp.alert_type, credibility=resp.credibility,
    )
    alert = _build_alert(message, analysis)
    payload = alert.model_dump(mode="json")
    database.save_alert(payload)
    _broadcast(payload)
    resp.alert_created = True
    resp.alert_id = alert.alert_id


def _media_type_of(url: str | None) -> str | None:
    ext = os.path.splitext((url or "").split("?")[0])[1].lower()
    if ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        return "video"
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}:
        return "image"
    return None


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket) -> None:
    """Dashboard subscribes here to get new alerts pushed the instant they're created.

    On connect we replay the current alerts so a freshly (re)connected dashboard is
    instantly in sync — important on Render free tier, where cold starts drop sockets.
    When the socket is idle we send a heartbeat ping so proxies don't close it.
    """
    await ws.accept()
    _ws_locks[ws] = asyncio.Lock()
    for alert in database.get_alerts():  # snapshot replay (client dedupes by alert_id)
        if not await _safe_send(ws, alert):
            break
    _ws_clients.add(ws)
    try:
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=WS_HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                if not await _safe_send(ws, {"type": "ping"}):  # heartbeat; stop if dead
                    break
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(ws)
        _ws_locks.pop(ws, None)


async def _safe_send(ws: WebSocket, data: dict) -> bool:
    """Send JSON under the socket's lock so concurrent broadcasts can't interleave frames."""
    lock = _ws_locks.get(ws)
    if lock is None:
        return False
    try:
        async with lock:
            await ws.send_json(data)
        return True
    except Exception:  # noqa: BLE001 — caller drops the dead client
        return False


# ---- demo data ----
def _seed_from_mock() -> int:
    """Clear all alerts and load the demo set (contract C) from mock_alerts.json."""
    database.clear_alerts()
    with open(_MOCK_ALERTS_PATH, encoding="utf-8") as f:
        raw_alerts = json.load(f)
    for raw in raw_alerts:
        payload = Alert.model_validate(raw).model_dump(mode="json")  # enforce contract C
        database.save_alert(payload)
        _broadcast(payload)
    return len(raw_alerts)


# ---- realtime push ----
def _broadcast(alert: dict) -> None:
    """Fire-and-forget from the sync /ingest path; schedules the send on the main loop."""
    if _loop is None or not _ws_clients:
        return
    asyncio.run_coroutine_threadsafe(_async_broadcast(alert), _loop)


async def _async_broadcast(alert: dict) -> None:
    for ws in list(_ws_clients):
        if not await _safe_send(ws, alert):  # per-socket lock; drop clients that error
            _ws_clients.discard(ws)
            _ws_locks.pop(ws, None)


# ---- helpers ----
def _analyze(message: IncomingMessage) -> AnalysisResult:
    if _analyzer is not None:
        return _analyzer.analyze(message)
    return AnalysisResult(  # stub keeps the pipe alive if Dev 1 isn't merged yet
        message_id=message.message_id, is_toxic=False, toxicity_score=0.0,
        category="none", role_of_child="none", explanation="analyzer stub",
        model_used="stub",
    )


def _disinfo_analysis(message: IncomingMessage) -> AnalysisResult | None:
    """Fact-check the message text; return a disinformation result if it's not credible.

    has_media is deliberately False: a plain photo must NOT be auto-flagged as fake —
    media authenticity (deepfake/AI) is the vision model's separate job. The threshold
    keeps benign chatter out (the heuristic only dips low on suspicious-forward phrasing).
    """
    if check_claim is None:
        return None
    try:
        cred = check_claim(message.text, has_media=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[backend] disinfo fact_check failed: {exc}")
        return None
    if cred is None or cred.score >= DISINFO_THRESHOLD:
        return None
    return AnalysisResult(
        message_id=message.message_id,
        is_toxic=False,
        toxicity_score=round(1.0 - cred.score, 3),  # disinfo "risk" drives the severity colour
        category="disinformation",
        role_of_child="exposed",
        explanation=f"disinformation: {cred.verdict} (credibility={cred.score:.2f})",
        model_used="fact_check",
        alert_type="disinformation",
        credibility=cred,
    )


def _build_alert(message: IncomingMessage, analysis: AnalysisResult) -> Alert:
    recommendation = _recommend(message, analysis)
    severity = severity_from_score(analysis.toxicity_score)
    return Alert(
        alert_id=f"alert_{uuid.uuid4().hex[:8]}",
        child_id=message.child_id,
        severity=severity,
        toxicity_score=analysis.toxicity_score,
        role_of_child=analysis.role_of_child,
        category=analysis.category,
        group_name=message.group_name,
        trigger_message=ChatBubble(
            sender_name=message.sender_name, text=message.text, timestamp=message.timestamp,
            media_url=message.media_url, media_type=message.media_type,
        ),
        context_before=[ChatBubble(sender_name="?", text=t) for t in message.context_before],
        context_after=[ChatBubble(sender_name="?", text=t) for t in message.context_after],
        recommendation=recommendation,
        created_at=datetime.now(),
        # New (contract v2): severe categories -> police banner; disinfo -> credibility.
        alert_type=analysis.alert_type,
        escalation=escalation_from(analysis.category, severity),
        credibility=_credibility(message, analysis),
    )


def _credibility(message: IncomingMessage, analysis: AnalysisResult):
    """Prefer the analysis's own credibility; else fact-check disinformation as a fallback."""
    if analysis.credibility is not None:
        return analysis.credibility
    if analysis.alert_type == "disinformation" and check_claim is not None:
        try:
            # has_media=False on purpose: media presence alone must not imply "fake".
            return check_claim(message.text, has_media=False)
        except Exception as exc:  # noqa: BLE001
            print(f"[backend] fact_check failed: {exc}")
    return None


def _recommend(message: IncomingMessage, analysis: AnalysisResult) -> str:
    if generate_recommendation is not None:
        try:
            return generate_recommendation(analysis, message)
        except Exception as exc:  # noqa: BLE001
            print(f"[backend] recommendation failed, using default: {exc}")
    return "זוהה אירוע בעייתי. מומלץ לשוחח עם הילד בנחת ולבדוק את ההקשר."
