"""
ML Service orchestrator. OWNER: Dev 1.

This is the backend-facing black box:
    IncomingMessage -> ToxicityAnalyzer.analyze() -> AnalysisResult

Task-specific analyzers live in separate modules:
  - TextToxicityAnalyzer: Hebrew text/context toxicity.
  - MediaAnalyzer: media_url download + image/video safety.
  - role_classifier.py: category and child role.

The public contract stays unchanged so the backend can keep importing
ToxicityAnalyzer from this file.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import AnalysisResult, IncomingMessage  # noqa: E402
from ml_service.role_classifier import classify_category, classify_role  # noqa: E402
from ml_service.text_analyzer import (  # noqa: E402
    TOXIC_THRESHOLD,
    TextAnalysis,
    TextToxicityAnalyzer,
)
from ml_service.vision import MediaAnalysis, MediaAnalyzer  # noqa: E402


@dataclass
class CombinedAnalysis:
    """Internal merged score before conversion to AnalysisResult."""

    score: float
    category: str
    text: TextAnalysis
    media: MediaAnalysis | None


class ToxicityAnalyzer:
    """Compose text, media, role, and category analyzers."""

    def __init__(self, use_model: bool = True, use_vision: bool = True):
        self.text_analyzer = TextToxicityAnalyzer(use_model=use_model)
        self.media_analyzer = MediaAnalyzer(use_model=False) if use_vision else None

        # Compatibility aliases for older tests/code that accessed these fields.
        self.vision = self.media_analyzer
        self.model_name = self.text_analyzer.model_name

    def analyze(self, message: IncomingMessage) -> AnalysisResult:
        """Analyze one incoming message and always return AnalysisResult."""
        try:
            combined = self._analyze_content(message)
            is_toxic = combined.score >= TOXIC_THRESHOLD
            role = classify_role(message, is_toxic)
            explanation = self._explain(combined, role)

            return AnalysisResult(
                message_id=message.message_id,
                is_toxic=is_toxic,
                toxicity_score=round(combined.score, 3),
                category=combined.category if is_toxic else "none",
                role_of_child=role,
                aggressor=message.sender_id if role == "aggressor" else None,
                victim=message.child_id if role == "victim" else None,
                explanation=explanation,
                model_used=self._model_used(combined.media),
            )
        except Exception as exc:
            print(f"[analyzer] analysis failed, returning safe fallback: {exc}")
            return self._safe_result(message)

    def _analyze_content(self, message: IncomingMessage) -> CombinedAnalysis:
        """Run task analyzers and merge their scores."""
        text = self.text_analyzer.analyze(message)
        media = self._analyze_media(message)

        media_score = media.score if media is not None else 0.0
        score = max(text.score, media_score)

        if media is not None and media.is_harmful and media_score >= text.score:
            category = media.category
        elif score >= TOXIC_THRESHOLD:
            category = classify_category(message.text)
        else:
            category = "none"

        return CombinedAnalysis(score=score, category=category, text=text, media=media)

    def _analyze_media(self, message: IncomingMessage) -> MediaAnalysis | None:
        """Analyze media_url when present."""
        # Keep self.vision as the writable alias used by tests.
        media_analyzer = self.vision
        if not message.media_url or media_analyzer is None:
            return None
        return media_analyzer.analyze_url(message.media_url)

    def _explain(self, combined: CombinedAnalysis, role: str) -> str:
        """Build a compact machine-readable explanation."""
        level = TextToxicityAnalyzer.toxicity_level(combined.score)
        explanation = (
            f"{level}: category={combined.category}, role={role}, "
            f"score={combined.score:.2f}, text_score={combined.text.score:.2f}, "
            f"threshold={TOXIC_THRESHOLD:.2f}"
        )
        if combined.media is not None:
            explanation += (
                f", media_score={combined.media.score:.2f}, "
                f"media={combined.media.explanation}"
            )
        return explanation

    def _model_used(self, media: MediaAnalysis | None) -> str:
        text_model = self.text_analyzer.model_name
        if media is None:
            return text_model
        return f"{text_model}; media={media.model_used}"

    def _safe_result(self, message: IncomingMessage) -> AnalysisResult:
        return AnalysisResult(
            message_id=message.message_id,
            is_toxic=False,
            toxicity_score=0.0,
            category="none",
            role_of_child="none",
            aggressor=None,
            victim=None,
            explanation="safe fallback after analyzer error",
            model_used="safe-fallback",
        )


if __name__ == "__main__":
    from datetime import datetime

    analyzer = ToxicityAnalyzer(use_model=True)
    msg = IncomingMessage(
        message_id="t1",
        group_name="כיתה ו'2 - עבודה במדעים",
        sender_id="dani_2",
        sender_name="דני",
        child_id="yonatan_1",
        text="כולם מעדיפים שתישאר בבית מחר, אל תבוא לחזרה ואל תכתוב בקבוצה השנייה.",
        timestamp=datetime.now(),
        context_before=[
            "כבר פתחנו קבוצה נפרדת בלי יונתן כדי שזה יתקדם מהר.",
            "לא חייבים לשתף אותו בכל דבר.",
            "אם הוא יבוא זה רק יפריע.",
        ],
        context_after=[
            "יונתן: אז אתם פשוט מוציאים אותי מהקבוצה?",
            "נועה: זה חרם, וזה ממש לא מתאים.",
            "דני: אני לא עובד איתו, נקודה.",
        ],
    )
    print(analyzer.analyze(msg).model_dump_json(indent=2))
