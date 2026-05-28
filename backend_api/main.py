"""
SafeNet Backend — the connecting brain. OWNER: Dev 2.

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
import uuid
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import (  # noqa: E402
    Alert, AnalysisResult, ChatBubble, IncomingMessage, severity_from_score,
)
from backend_api import database  # noqa: E402

# Tunable at runtime via env vars — no code edit needed to flip the model on stage.
#   USE_MODEL=true   -> load the real HF model (keyword fallback if it fails to load)
#   ALERT_THRESHOLD  -> min toxicity score to raise an alert (0.5 matches severity_from_score)
USE_MODEL = os.getenv("USE_MODEL", "false").lower() == "true"
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.5"))

# ---- black-box deps (graceful import: demo runs even if a teammate's module is missing) ----
try:
    from ml_service.analyzer import ToxicityAnalyzer
    _analyzer = ToxicityAnalyzer(use_model=USE_MODEL)  # flip via USE_MODEL once ML pair is ready
except Exception as exc:  # noqa: BLE001
    print(f"[backend] analyzer unavailable, using stub: {exc}")
    _analyzer = None

try:
    from simulator_and_logic.recommendation_engine import generate_recommendation
except Exception as exc:  # noqa: BLE001
    print(f"[backend] recommendation engine unavailable, using stub: {exc}")
    generate_recommendation = None

app = FastAPI(title="SafeNet API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# Connected dashboards for real-time alert push. Polling /alerts still works in parallel.
_ws_clients: set[WebSocket] = set()
_loop: asyncio.AbstractEventLoop | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _loop
    database.init_db()
    _loop = asyncio.get_running_loop()  # captured so the sync /ingest can broadcast onto it


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "analyzer": getattr(_analyzer, "model_name", "stub"),
        "use_model": USE_MODEL,
        "alert_threshold": ALERT_THRESHOLD,
    }


@app.post("/ingest")
def ingest(message: IncomingMessage) -> dict[str, object]:
    """Receive one chat message, analyze it, raise an alert if toxic."""
    analysis = _analyze(message)
    if not analysis.is_toxic or analysis.toxicity_score < ALERT_THRESHOLD:
        return {"alert_created": False, "toxicity_score": analysis.toxicity_score}

    alert = _build_alert(message, analysis)
    payload = alert.model_dump(mode="json")
    database.save_alert(payload)
    _broadcast(payload)
    return {"alert_created": True, "alert_id": alert.alert_id}


@app.get("/alerts")
def list_alerts(child_id: str | None = None) -> list[dict]:
    """Feed for the parent dashboard (contract C)."""
    return database.get_alerts(child_id)


@app.post("/demo/seed")
def demo_seed() -> dict[str, int]:
    """Reset to a clean 3-angle demo set (contracts/mock_alerts.json). Idempotent."""
    database.clear_alerts()
    path = os.path.join(os.path.dirname(__file__), "..", "contracts", "mock_alerts.json")
    with open(path, encoding="utf-8") as f:
        alerts = json.load(f)
    for alert in alerts:
        database.save_alert(alert)
    return {"seeded": len(alerts)}


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket) -> None:
    """Dashboard subscribes here to get new alerts pushed the instant they're created."""
    await ws.accept()
    _ws_clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep the socket open; inbound messages are ignored
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(ws)


# ---- realtime push ----
def _broadcast(alert: dict) -> None:
    """Fire-and-forget from the sync /ingest path; schedules the send on the main loop."""
    if _loop is None or not _ws_clients:
        return
    asyncio.run_coroutine_threadsafe(_async_broadcast(alert), _loop)


async def _async_broadcast(alert: dict) -> None:
    dead = []
    for ws in list(_ws_clients):
        try:
            await ws.send_json(alert)
        except Exception:  # noqa: BLE001 — drop clients that have gone away
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


# ---- helpers ----
def _analyze(message: IncomingMessage) -> AnalysisResult:
    if _analyzer is not None:
        return _analyzer.analyze(message)
    return AnalysisResult(  # stub keeps the pipe alive if Dev 1 isn't merged yet
        message_id=message.message_id, is_toxic=False, toxicity_score=0.0,
        category="none", role_of_child="none", explanation="analyzer stub",
        model_used="stub",
    )


def _build_alert(message: IncomingMessage, analysis: AnalysisResult) -> Alert:
    recommendation = _recommend(message, analysis)
    return Alert(
        alert_id=f"alert_{uuid.uuid4().hex[:8]}",
        child_id=message.child_id,
        severity=severity_from_score(analysis.toxicity_score),
        toxicity_score=analysis.toxicity_score,
        role_of_child=analysis.role_of_child,
        category=analysis.category,
        group_name=message.group_name,
        trigger_message=ChatBubble(
            sender_name=message.sender_name, text=message.text, timestamp=message.timestamp
        ),
        context_before=[ChatBubble(sender_name="?", text=t) for t in message.context_before],
        context_after=[ChatBubble(sender_name="?", text=t) for t in message.context_after],
        recommendation=recommendation,
        created_at=datetime.now(),
    )


def _recommend(message: IncomingMessage, analysis: AnalysisResult) -> str:
    if generate_recommendation is not None:
        try:
            return generate_recommendation(analysis, message)
        except Exception as exc:  # noqa: BLE001
            print(f"[backend] recommendation failed, using default: {exc}")
    return "זוהה אירוע בעייתי. מומלץ לשוחח עם הילד בנחת ולבדוק את ההקשר."
