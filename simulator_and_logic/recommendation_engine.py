"""
Recommendation engine — the killer feature. OWNER: Dev 4.

Turns an AnalysisResult + context into an empathetic, pedagogical recommendation
for the parent. Imported as a black box by the backend.

Strategy: call an LLM with a tight system prompt. Fall back to a templated
recommendation if no API key / the call fails — the demo never shows an empty box.
"""
from __future__ import annotations

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import AnalysisResult, IncomingMessage  # noqa: E402

SYSTEM_PROMPT = """אתה יועץ חינוכי מומחה לבריונות ברשת, פונה להורה בעברית.
ההורה קיבל התראה על הילד שלו. כתוב המלצה של 2-3 משפטים בלבד:
1. פתח בהכרה רגשית קצרה במצב (בלי דרמה, בלי להבהיל).
2. תן צעד פעולה אחד קונקרטי שההורה יכול לעשות היום.
3. שמור על טון תומך — אל תאשים את ההורה או הילד.

התאם את ההמלצה לתפקיד הילד:
- קורבן: חזק תחושת ביטחון, אל תייחס אשמה לילד, שקול פנייה לגורם בבית הספר.
- תוקף: בלי הענשה מיידית — עזור לילד להבין את ההשפעה על הצד השני, עודד תיקון.
- צופה מהצד: עודד את הילד לא להישאר אדיש ולתמוך בנפגע.

בלי ז'רגון מקצועי, בלי רשימות, בלי הקדמות. רק ההמלצה עצמה."""

# Templated fall-backs by role (used when LLM unavailable).
_FALLBACK = {
    "victim": "הילד שלך היה קורבן. שוחח איתו בנחת, שאל איך הרגיש, והבהר שזו לא אשמתו. שקול פנייה למחנכת.",
    "aggressor": "הילד שלך פגע באחר. שוחח בלי להאשים, עזור לו להבין את ההשפעה על הצד השני, ועודד תיקון.",
    "bystander": "הילד שלך נכח באירוע פגיעה. שאל מה ראה, הסבר שאדישות מזיקה, ועודד אותו לתמוך בנפגע.",
    "none": "זוהה אירוע בעייתי. מומלץ לעקוב ולשוחח עם הילד על מה שקורה בקבוצה.",
}


def generate_recommendation(analysis: AnalysisResult, message: IncomingMessage) -> str:
    """Always returns a non-empty string. Never raises."""
    try:
        return _llm_recommendation(analysis, message)
    except Exception as exc:  # noqa: BLE001
        print(f"[reco] LLM failed, using template: {exc}")
        return _FALLBACK.get(analysis.role_of_child, _FALLBACK["none"])


def _llm_recommendation(analysis: AnalysisResult, message: IncomingMessage) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("no ANTHROPIC_API_KEY set")

    from anthropic import Anthropic  # local import: optional dep

    client = Anthropic(api_key=api_key)
    user_msg = (
        f"תפקיד הילד: {analysis.role_of_child}\n"
        f"קטגוריה: {analysis.category}\n"
        f"ציון רעילות: {analysis.toxicity_score}\n"
        f"קבוצה: {message.group_name}\n"
        f"ההודעה: \"{message.text}\"\n"
        f"קונטקסט קודם: {message.context_before}\n"
        "כתוב המלצה להורה."
    )
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text.strip()


if __name__ == "__main__":
    from datetime import datetime

    a = AnalysisResult(
        message_id="t1", is_toxic=True, toxicity_score=0.9, category="harassment",
        role_of_child="victim", explanation="test", model_used="test",
    )
    m = IncomingMessage(
        message_id="t1", group_name="טסט", sender_id="dani", sender_name="דני",
        child_id="yon", text="איזה אפס אתה", timestamp=datetime.now(),
    )
    print(generate_recommendation(a, m))
