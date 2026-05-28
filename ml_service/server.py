"""
Standalone ML service — runs the REAL models on a powerful local machine and is
exposed via ngrok. Render's backend forwards analysis here when USE_MODEL=true and
ML_SERVICE_URL is set, so Render stays light (no torch) while judges still get real
OpenCensor toxicity / NSFW / deepfake scores.

Run (use Python 3.11 or 3.12 — NOT 3.14; torch wheels):
    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r ml_service/requirements.txt
    uvicorn ml_service.server:app --host 0.0.0.0 --port 8100
    ngrok http 8100            # copy the https URL
    # then on Render set:  USE_MODEL=true  and  ML_SERVICE_URL=https://<id>.ngrok.app

Contract: returns contracts.schemas.AnalyzeResponse (the backend adds
credibility/alert on top). The first call downloads the HF models — warm it up
before the demo by hitting /analyze once.
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import AnalyzeResponse, IncomingMessage, MediaReport  # noqa: E402
from ml_service.analyzer import ToxicityAnalyzer  # noqa: E402

app = FastAPI(title="SafeNet ML Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load the real models. Text model loads now; media models load lazily on first media.
_analyzer = ToxicityAnalyzer(use_model=True, use_vision=True)

_VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


class AnalyzeRequest(BaseModel):
    text: str = ""
    media_url: str | None = None


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "text_model": _analyzer.model_name, "use_model": True}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    msg = _message(req.text, req.media_url, _media_type_of(req.media_url))
    return _report(msg)


@app.post("/analyze/upload", response_model=AnalyzeResponse)
async def analyze_upload(text: str = Form(""), file: UploadFile | None = File(None)) -> AnalyzeResponse:
    media_type, tmp_path = None, None
    if file is not None and file.filename:
        suffix = os.path.splitext(file.filename)[1].lower() or ".bin"
        media_type = "video" if suffix in _VIDEO_EXT else "image"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as out:
            out.write(await file.read())
    try:
        msg = _message(text, None, media_type)
        return await asyncio.to_thread(_report, msg, tmp_path, media_type)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _report(message: IncomingMessage, upload_path: str | None = None,
            upload_media_type: str | None = None) -> AnalyzeResponse:
    """Run the real text + media models and assemble an AnalyzeResponse."""
    media_analysis, media_type = None, None
    if upload_path:
        media_analysis = _safe(lambda: _analyzer.vision.analyze_path(Path(upload_path)))
        media_type = upload_media_type
    elif message.media_url and _analyzer.vision is not None:
        media_analysis = _safe(lambda: _analyzer.vision.analyze_url(message.media_url))
        media_type = message.media_type or _media_type_of(message.media_url)

    ar = _analyzer.analyze(message)  # AnalysisResult (text, or text+url combined)
    is_toxic, score, category = ar.is_toxic, ar.toxicity_score, ar.category

    media = None
    if media_analysis is not None:
        media = MediaReport(
            media_type=media_type, safety_score=media_analysis.safety_score,
            ai_score=media_analysis.ai_score, is_harmful=media_analysis.is_harmful,
            model_used=media_analysis.model_used, explanation=media_analysis.explanation,
        )
        if media_analysis.is_harmful:
            is_toxic = True
            score = max(score, media_analysis.safety_score)
            if media_analysis.safety_score >= ar.toxicity_score:
                category = "sexual"

    return AnalyzeResponse(
        is_toxic=is_toxic, toxicity_score=round(score, 3),
        category=category if is_toxic else "none", role_of_child=ar.role_of_child,
        alert_type=ar.alert_type, explanation=ar.explanation,
        model_used=ar.model_used, media=media,
    )


def _message(text, media_url, media_type) -> IncomingMessage:
    return IncomingMessage(
        message_id="ml", group_name="ml", sender_id="judge", sender_name="Judge",
        child_id="judge", text=text or "", media_url=media_url or None,
        media_type=media_type or None, timestamp=datetime.now(),
    )


def _media_type_of(url: str | None) -> str | None:
    ext = os.path.splitext((url or "").split("?")[0])[1].lower()
    if ext in _VIDEO_EXT:
        return "video"
    if ext in _IMAGE_EXT:
        return "image"
    return None


def _safe(fn):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        print(f"[ml] media analysis failed: {exc}")
        return None
