"""
SafeNet Backend — the connecting brain. OWNER: Dev 2.

Flow:
  Simulator --POST /ingest--> [analyze] --if toxic--> [recommend] --> save Alert
  Frontend  --GET  /alerts--> list of Alerts (contract C)

ML (Dev 1) and recommendation engine (Dev 4) are imported as black boxes.
Both calls are wrapped so a failure degrades gracefully instead of crashing the demo.

Run:  uvicorn main:app --reload --port 8000   (Swagger at /docs)
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import (  # noqa: E402
    Alert, AnalysisResult, ChatBubble, IncomingMessage, severity_from_score,
)
from backend_api import database  # noqa: E402

# ---- black-box deps (graceful import: demo runs even if a teammate's module is missing) ----
try:
    from ml_service.analyzer import ToxicityAnalyzer
    _analyzer = ToxicityAnalyzer(use_model=False)  # flip to True once Dev 1's model is ready
except Exception as exc:  # noqa: BLE001
    print(f"[backend] analyzer unavailable, using stub: {exc}")
    _analyzer = None

try:
    from simulator_and_logic.recommendation_engine import generate_recommendation
except Exception as exc:  # noqa: BLE001
    print(f"[backend] recommendation engine unavailable, using stub: {exc}")
    generate_recommendation = None

ALERT_THRESHOLD = 0.5

app = FastAPI(title="SafeNet API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
def _startup() -> None:
    database.init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(message: IncomingMessage) -> dict[str, object]:
    """Receive one chat message, analyze it, raise an alert if toxic."""
    analysis = _analyze(message)
    if not analysis.is_toxic or analysis.toxicity_score < ALERT_THRESHOLD:
        return {"alert_created": False, "toxicity_score": analysis.toxicity_score}

    alert = _build_alert(message, analysis)
    database.save_alert(alert.model_dump(mode="json"))
    return {"alert_created": True, "alert_id": alert.alert_id}


@app.get("/alerts")
def list_alerts(child_id: str | None = None) -> list[dict]:
    """Feed for the parent dashboard (contract C)."""
    return database.get_alerts(child_id)


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
