"""
Shared data contracts for ParAlert. SINGLE SOURCE OF TRUTH.

Every module imports these. Do NOT change a field without telling the whole team.
New fields are optional with defaults, so older data/code stays valid.
Pydantic models = runtime validation + auto Swagger docs in FastAPI.

Install: pip install pydantic
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---- Enums (as Literals, keep them in sync with Idea+Plan.md) ----
Role = Literal["aggressor", "victim", "bystander", "exposed", "none"]
Category = Literal[
    "harassment", "threat", "exclusion", "hate_speech",
    "sexual", "sexual_harassment", "nudity", "self_harm",
    "disinformation", "none",
]
Severity = Literal["low", "medium", "high"]
Escalation = Literal["none", "school", "police"]  # severe -> recommend police
AlertType = Literal["bullying", "disinformation"]
MediaType = Literal["image", "video"]

# Severe categories that warrant a police recommendation.
_POLICE_CATEGORIES = {"sexual", "sexual_harassment", "nudity", "self_harm"}


# ---- Contract A: incoming message (Simulator / Bridge -> Backend) ----
class IncomingMessage(BaseModel):
    message_id: str
    group_name: str
    sender_id: str
    sender_name: str
    child_id: str
    text: str
    media_url: Optional[str] = None
    media_type: Optional[MediaType] = None
    timestamp: datetime
    context_before: list[str] = Field(default_factory=list)
    context_after: list[str] = Field(default_factory=list)


# ---- Disinformation / AI-generated content assessment ----
class Credibility(BaseModel):
    score: float = Field(ge=0.0, le=1.0)  # 0 = fabricated/false, 1 = credible
    verdict: str                          # e.g. "תוכן מזויף (AI)", "טענה שגויה"
    claim: str                            # the claim / content assessed
    source: Optional[str] = None          # fact-check source / url


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
    alert_type: AlertType = "bullying"
    escalation: Escalation = "none"
    credibility: Optional[Credibility] = None


# ---- Contract C: alert object (Backend -> Frontend) ----
class ChatBubble(BaseModel):
    sender_name: str
    text: str
    timestamp: Optional[datetime] = None
    media_url: Optional[str] = None
    media_type: Optional[MediaType] = None


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
    alert_type: AlertType = "bullying"
    escalation: Escalation = "none"
    credibility: Optional[Credibility] = None


# ---- Interactive analysis report (Backend/ML service -> "Try it" playground) ----
class MediaReport(BaseModel):
    """Per-media model scores for the interactive playground."""
    media_type: Optional[MediaType] = None
    safety_score: float = 0.0   # unsafe/NSFW visual content
    ai_score: float = 0.0       # AI-generated / deepfake likelihood
    is_harmful: bool = False
    model_used: str = "none"
    explanation: str = ""


class AnalyzeResponse(BaseModel):
    """Full analysis report for one submitted message/media (no alert required)."""
    is_toxic: bool
    toxicity_score: float = Field(ge=0.0, le=1.0)
    category: Category
    role_of_child: Role = "none"
    alert_type: AlertType = "bullying"
    explanation: str = ""
    model_used: str = ""
    media: Optional[MediaReport] = None
    credibility: Optional[Credibility] = None
    alert_created: bool = False
    alert_id: Optional[str] = None


def severity_from_score(score: float) -> Severity:
    """Shared rule so backend + sim agree. <0.5 low, 0.5-0.8 medium, >0.8 high."""
    if score > 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def escalation_from(category: Category, severity: Severity) -> Escalation:
    """Severe categories (or a high-severity threat) -> recommend contacting police."""
    if category in _POLICE_CATEGORIES:
        return "police"
    if category == "threat" and severity == "high":
        return "police"
    return "none"
