"""
ML Service — toxicity analyzer. OWNER: Dev 1.

Black box for the backend. Input = IncomingMessage (contract A),
output = AnalysisResult (contract B). No HTTP here.

Strategy (see Idea+Plan.md §5):
  1. Try a HuggingFace toxicity model.
  2. Fall back to a keyword heuristic if the model fails to load (OOM / offline).
The backend never crashes because analyze() always returns a valid AnalysisResult.
"""
from __future__ import annotations

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import IncomingMessage, AnalysisResult  # noqa: E402

# Swap for "dicta-il/dictabert" + a fine-tuned head, or the multilingual model below.
HF_MODEL = "unitary/multilingual-toxic-xlm-roberta"

# Cheap Hebrew heuristic for the fall-back path. Expand freely.
_TOXIC_KEYWORDS = [
    "אפס", "מטומטם", "טמבל", "שמן", "מכוער", "דביל", "תמות",
    "אני מחכה לך", "כולם נגדך", "אל תבוא", "לא מזמינים", "מעצבן",
]


class ToxicityAnalyzer:
    def __init__(self, use_model: bool = True):
        self.model = None
        self.model_name = "keyword-fallback"
        if use_model:
            self._try_load_model()

    def _try_load_model(self) -> None:
        try:
            from transformers import pipeline  # local import: optional dep

            self.model = pipeline("text-classification", model=HF_MODEL, top_k=None)
            self.model_name = HF_MODEL
        except Exception as exc:  # OOM, no internet, missing dep — degrade gracefully
            print(f"[analyzer] model load failed, using fallback: {exc}")
            self.model = None

    def analyze(self, message: IncomingMessage) -> AnalysisResult:
        """Always returns a valid AnalysisResult. Never raises."""
        try:
            score = self._score(message.text)
        except Exception as exc:
            print(f"[analyzer] scoring failed, defaulting to 0: {exc}")
            score = 0.0

        is_toxic = score >= 0.5
        category = self._classify_category(message.text) if is_toxic else "none"
        role = self._classify_role(message, is_toxic)

        return AnalysisResult(
            message_id=message.message_id,
            is_toxic=is_toxic,
            toxicity_score=round(score, 3),
            category=category,
            role_of_child=role,
            aggressor=message.sender_id if role == "aggressor" else None,
            victim=message.child_id if role == "victim" else None,
            explanation=self._explain(category, role, score),
            model_used=self.model_name,
        )

    # ---- scoring ----
    def _score(self, text: str) -> float:
        if self.model is not None:
            results = self.model(text)[0]  # list of {label, score}
            toxic = [r["score"] for r in results if "toxic" in r["label"].lower()]
            return max(toxic) if toxic else 0.0
        # fallback: fraction of toxic keywords present, capped
        hits = sum(1 for kw in _TOXIC_KEYWORDS if kw in text)
        return min(0.6 + 0.15 * hits, 0.97) if hits else 0.1

    # ---- TODO Dev 1: replace heuristics with a real classifier head ----
    def _classify_category(self, text: str) -> str:
        if any(w in text for w in ["מחכה לך", "תמות", "אני אחכה"]):
            return "threat"
        if any(w in text for w in ["לא מזמינים", "כולם נגדך", "אל תבוא"]):
            return "exclusion"
        return "harassment"

    def _classify_role(self, message: IncomingMessage, is_toxic: bool) -> str:
        if not is_toxic:
            return "none"
        # If our child sent the toxic message -> aggressor. Else victim.
        # bystander logic (toxic msg between two others) = TODO Dev 1.
        return "aggressor" if message.sender_id == message.child_id else "victim"

    def _explain(self, category: str, role: str, score: float) -> str:
        return f"{category} זוהה (role={role}, score={score:.2f})"


if __name__ == "__main__":
    from datetime import datetime

    a = ToxicityAnalyzer(use_model=False)
    msg = IncomingMessage(
        message_id="t1", group_name="טסט", sender_id="dani_2",
        sender_name="דני", child_id="yonatan_1",
        text="איזה אפס אתה, אל תבוא מחר", timestamp=datetime.now(),
    )
    print(a.analyze(msg).model_dump_json(indent=2))
