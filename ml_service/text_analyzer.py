"""
Text toxicity analysis for Hebrew chat messages.

This module owns text-only ML logic:
  - Hugging Face Hebrew profanity/toxicity scoring.
  - Contextual bullying heuristics for exclusion, boycott, and threats.
  - Conversion of numeric scores into five safety levels.

It intentionally does not know about HTTP, media URLs, backend alerts, or child
role classification. Those responsibilities live in other modules.
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts.schemas import IncomingMessage

HF_MODEL = "LikoKIko/OpenCensor-H1"
HF_MAX_TOKENS = 512
TOXIC_THRESHOLD = 0.49

_TOXIC_KEYWORDS = [
    "אפס", "מטומטם", "טמבל", "שמן", "מכוער", "דביל", "תמות",
    "אני מחכה לך", "כולם נגדך", "אל תבוא", "לא מזמינים", "מעצבן",
    "אף אחד לא רוצה אותך", "לך מפה", "סתום", "חנון", "לוזר",
]

_EXCLUSION_PHRASES = [
    "אל תבוא", "אל תזמינו", "לא צריך שתבוא", "תישאר בבית",
    "אף אחד לא רוצה אותך", "כולם מעדיפים", "כולם חוץ", "כולם נגדך",
    "לא מזמינים", "בלי יונתן", "בלי רועי", "קבוצה נפרדת",
    "קבוצה שנייה", "קבוצה בלי", "נפתח קבוצה בלי", "לא עובד איתו",
    "לא עובדים איתו", "שלא יבוא", "לא לשתף אותך",
    "מוציאים אותי מהקבוצה", "זה חרם", "עדיף שלא תציג",
    "יותר טוב לכולם", "מישהו אחר ידבר במקומו", "רק לשלוח את הסיכום",
]

_THREAT_PHRASES = [
    "אני מחכה לך", "אחרי בית ספר", "תיזהר", "אם תספר", "תמות",
]

_SAFE_CONTEXT_PHRASES = [
    "בסוף נפגשים", "כולם מוזמנים", "תביא את", "נפגשים בכיתה", "לא בספרייה",
]

_AMBIGUOUS_LOGISTICS_PHRASES = [
    "אל תבוא",
]


@dataclass
class TextAnalysis:
    """Text analysis result used by the orchestrator."""

    score: float
    level: str
    model_used: str


class TextToxicityAnalyzer:
    """Score Hebrew text and surrounding context for bullying/toxicity."""

    def __init__(self, use_model: bool = True):
        """Create the analyzer and optionally load the Hugging Face model."""
        self.model = None
        self.tokenizer = None
        self.torch = None
        self.model_name = "keyword-fallback"
        if use_model:
            self._try_load_model()

    def _try_load_model(self) -> None:
        """Load OpenCensor-H1 tokenizer and model from Hugging Face."""
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(HF_MODEL)
            self.model = AutoModelForSequenceClassification.from_pretrained(HF_MODEL).eval()
            self.torch = torch
            self.model_name = HF_MODEL
        except Exception as exc:
            print(f"[text] model load failed, using fallback: {exc}")
            self.model = None
            self.tokenizer = None
            self.torch = None
            self.model_name = "keyword-fallback"

    def analyze(self, message: IncomingMessage) -> TextAnalysis:
        """Analyze message.text together with its before/after context."""
        text = self.build_context_text(message)
        score = self.score_text(text)
        return TextAnalysis(
            score=score,
            level=self.toxicity_level(score),
            model_used=self.model_name,
        )

    def score_text(self, text: str) -> float:
        """Return a toxicity score between 0.0 and 1.0."""
        heuristic_score = self._heuristic_score(text)

        if self.model is None or self.tokenizer is None or self.torch is None:
            return heuristic_score

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=HF_MAX_TOKENS,
        )
        with self.torch.inference_mode():
            logits = self.model(**inputs).logits

        if logits.numel() == 1:
            model_score = float(self.torch.sigmoid(logits).item())
        else:
            probabilities = self.torch.softmax(logits, dim=-1)[0]
            model_score = float(probabilities[1:].max().item())

        return max(model_score, heuristic_score)

    def _heuristic_score(self, text: str) -> float:
        """Score bullying patterns that profanity-only models often miss."""
        hits = sum(1 for phrase in _TOXIC_KEYWORDS if phrase in text)
        exclusion_hits = sum(1 for phrase in _EXCLUSION_PHRASES if phrase in text)
        threat_hits = sum(1 for phrase in _THREAT_PHRASES if phrase in text)
        safe_context_hits = sum(1 for phrase in _SAFE_CONTEXT_PHRASES if phrase in text)

        # Example: "don't come to the library, we meet in class" is logistical,
        # not bullying. These guards reduce that false positive.
        if exclusion_hits == 1 and safe_context_hits >= 2 and not hits and not threat_hits:
            exclusion_hits = 0
        if safe_context_hits >= 2 and not threat_hits:
            hits -= sum(1 for phrase in _AMBIGUOUS_LOGISTICS_PHRASES if phrase in text)
            hits = max(hits, 0)
            if exclusion_hits == 1:
                exclusion_hits = 0

        scores = [0.1]
        if hits:
            scores.append(min(0.6 + 0.15 * hits, 0.97))
        if exclusion_hits:
            scores.append(min(0.55 + 0.08 * exclusion_hits, 0.92))
        if threat_hits:
            scores.append(min(0.7 + 0.1 * threat_hits, 0.97))

        return max(scores)

    def build_context_text(self, message: IncomingMessage) -> str:
        """Combine context_before, message.text, and context_after."""
        parts = [*message.context_before, message.text, *message.context_after]
        return "\n".join(part for part in parts if part)

    @staticmethod
    def toxicity_level(score: float) -> str:
        """Map a numeric score into one of five stable severity labels."""
        if score < 0.2:
            return "level_1_safe"
        if score < 0.4:
            return "level_2_mild"
        if score < 0.6:
            return "level_3_concerning"
        if score < 0.8:
            return "level_4_toxic"
        return "level_5_severe"
