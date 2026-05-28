"""
Fact-check / credibility helper. OWNER: FS-B (disinformation track).

Given a claim/text (+ whether it carries media), returns a Credibility assessment
(contract C sub-model). Strategy: Google Fact Check Tools API if a key exists;
otherwise a keyword heuristic so the demo never breaks. AI-generated image/video
detection is a separate ML task (see WORKPLAN) — here we score the textual claim.

Imported as a black box by the backend for disinformation alerts.
"""
from __future__ import annotations

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import Credibility  # noqa: E402

GOOGLE_FACTCHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# Cheap signals that a forwarded message is likely disinformation.
_SUSPICIOUS = ["חייבים לשתף", "תפיצו", "דחוף", "הוכחה", "deepfake", "פייק", "האמת ש"]


def check_claim(text: str, has_media: bool = False) -> Credibility:
    """Always returns a Credibility. Never raises."""
    try:
        return _google_factcheck(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[fact_check] API unavailable, using heuristic: {exc}")
        return _heuristic(text, has_media)


def _google_factcheck(text: str) -> Credibility:
    key = os.environ.get("GOOGLE_FACTCHECK_API_KEY")
    if not key:
        raise RuntimeError("no GOOGLE_FACTCHECK_API_KEY set")

    import requests  # local import: optional dep

    r = requests.get(GOOGLE_FACTCHECK_URL, params={"query": text, "key": key}, timeout=10)
    claims = r.json().get("claims", [])
    if not claims:
        raise RuntimeError("no fact-check match")
    review = claims[0]["claimReview"][0]
    rating = (review.get("textualRating") or "").strip()
    is_false = any(w in rating.lower() for w in ("false", "fake", "misleading", "שגוי", "כוזב"))
    return Credibility(
        score=0.15 if is_false else 0.7,
        verdict=rating or "נבדק עובדתית",
        claim=text[:200],
        source=review.get("url") or "Google Fact Check Tools",
    )


def _heuristic(text: str, has_media: bool) -> Credibility:
    suspicious = has_media or any(s in text for s in _SUSPICIOUS)
    if suspicious:
        return Credibility(
            score=0.2,
            verdict="חשד לתוכן כוזב / מזויף",
            claim=text[:200],
            source="היוריסטיקה (stub)",
        )
    return Credibility(
        score=0.8,
        verdict="לא זוהתה בעיית אמינות",
        claim=text[:200],
        source="היוריסטיקה (stub)",
    )


if __name__ == "__main__":
    print(check_claim("חייבים לשתף!! הסרטון הזה מוכיח ש...", has_media=True).model_dump_json(indent=2))
    print(check_claim("נתראה מחר באימון").model_dump_json(indent=2))
