"""
Shared data contracts for SafeNet. SINGLE SOURCE OF TRUTH.

Every module imports these. Do NOT change a field without telling the whole team.
Pydantic models = runtime validation + auto Swagger docs in FastAPI.

Install: pip install pydantic
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---- Enums (as Literals, keep them in sync with Idea+Plan.md) ----
Role = Literal["aggressor", "victim", "bystander", "none"]
Category = Literal[
    "harassment", "threat", "exclusion", "hate_speech", "sexual", "none"
]
Severity = Literal["low", "medium", "high"]


# ---- Contract A: incoming message (Simulator -> Backend) ----
class IncomingMessage(BaseModel):
    message_id: str
    group_name: str
    sender_id: str
    sender_name: str
    child_id: str
    text: str
    media_url: Optional[str] = None
    timestamp: datetime
    context_before: list[str] = Field(default_factory=list)
    context_after: list[str] = Field(default_factory=list)


# ---- Contract B: analysis result (ML Service -> Backend) ----
class AnalysisResult(BaseModel):
    message_id: str
    is_toxic: bool
    toxicity_score: float = Field(ge=0.0, le=1.0)
    category: Category
    role_of_child: Role
    aggressor: Optional[str] = None
    victim: Optional[str] = None
    explanation: str
    model_used: str


# ---- Contract C: alert object (Backend -> Frontend) ----
class ChatBubble(BaseModel):
    sender_name: str
    text: str
    timestamp: Optional[datetime] = None


class Alert(BaseModel):
    alert_id: str
    child_id: str
    severity: Severity
    toxicity_score: float
    role_of_child: Role
    category: Category
    group_name: str
    trigger_message: ChatBubble
    context_before: list[ChatBubble] = Field(default_factory=list)
    context_after: list[ChatBubble] = Field(default_factory=list)
    recommendation: str
    created_at: datetime


def severity_from_score(score: float) -> Severity:
    """Shared rule so backend + sim agree. <0.5 low, 0.5-0.8 medium, >0.8 high."""
    if score > 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"
