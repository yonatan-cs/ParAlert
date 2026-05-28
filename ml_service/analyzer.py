"""
Backend-facing ML service facade.

The backend imports ToxicityAnalyzer from this module and treats it as a black
box. The public contract remains:

    IncomingMessage -> ToxicityAnalyzer.analyze() -> AnalysisResult

Task-specific logic lives in smaller analyzers:
  - TextToxicityAnalyzer: Hebrew text/context toxicity.
  - MediaAnalyzer: optional media_url image/video safety.
  - role_classifier.py: child role and text category.

The facade is defensive by design. Model loading, media downloads, and scoring
must never crash the backend demo; unexpected failures return a valid safe
AnalysisResult.
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
    """Internal merged result before conversion to AnalysisResult."""

    score: float
    category: str
    text: TextAnalysis
    media: MediaAnalysis | None


class ToxicityAnalyzer:
    """Compose text, media, role, and category analysis.

    Args:
        use_model: Load the text Hugging Face model when True. If it fails,
            the text analyzer falls back to deterministic keyword heuristics.
        use_vision: Enable media_url analysis when True. Media models are
            loaded lazily only when a message contains media.
    """

    def __init__(self, use_model: bool = True, use_vision: bool = True):
        self.text_analyzer = TextToxicityAnalyzer(use_model=use_model)
        self.media_analyzer = MediaAnalyzer(use_model=False) if use_vision else None

        # Compatibility aliases for older backend/dev code.
        self.vision = self.media_analyzer
        self.model_name = self.text_analyzer.model_name

    def analyze(self, message: IncomingMessage) -> AnalysisResult:
        """Analyze one incoming message and always return AnalysisResult."""
        try:
            combined = self._analyze_content(message)
            is_toxic = combined.score >= TOXIC_THRESHOLD
            role = classify_role(message, is_toxic)

            return AnalysisResult(
                message_id=message.message_id,
                is_toxic=is_toxic,
                toxicity_score=round(combined.score, 3),
                category=combined.category if is_toxic else "none",
                role_of_child=role,
                aggressor=message.sender_id if role == "aggressor" else None,
                victim=message.child_id if role == "victim" else None,
                explanation=self._explain(combined, role),
                model_used=self._model_used(combined_media=combined.media),
            )
        except Exception as exc:
            print(f"[analyzer] analysis failed, returning safe fallback: {exc}")
            return self._safe_result(message)

    def _analyze_content(self, message: IncomingMessage) -> CombinedAnalysis:
        """Run text/media analyzers and choose the strongest signal."""
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
        """Analyze message.media_url when media analysis is enabled."""
        if not message.media_url or self.vision is None:
            return None
        return self.vision.analyze_url(message.media_url)

    def _explain(self, combined: CombinedAnalysis, role: str) -> str:
        """Build a compact explanation for logs, API output, and the dashboard."""
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

    def _model_used(self, combined_media: MediaAnalysis | None) -> str:
        """Return a readable model list for the shared AnalysisResult field."""
        text_model = self.text_analyzer.model_name
        if combined_media is None:
            return text_model
        return f"{text_model}; media={combined_media.model_used}"

    def _safe_result(self, message: IncomingMessage) -> AnalysisResult:
        """Return a valid non-toxic result after an unexpected failure."""
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
