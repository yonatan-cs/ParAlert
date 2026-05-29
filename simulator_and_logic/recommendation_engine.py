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
from contracts.schemas import (  # noqa: E402
    AnalysisResult, IncomingMessage, escalation_from, severity_from_score,
)

SYSTEM_PROMPT = """אתה יועץ חינוכי מומחה לבריונות ברשת, פונה להורה בעברית.
ההורה קיבל התראה על הילד שלו. כתוב המלצה של 2-3 משפטים בלבד:
1. פתח בהכרה רגשית קצרה במצב (בלי דרמה, בלי להבהיל).
2. תן צעד פעולה אחד קונקרטי שההורה יכול לעשות היום.
3. שמור על טון תומך — אל תאשים את ההורה או הילד.

התאם את ההמלצה לתפקיד הילד:
- קורבן: חזק תחושת ביטחון, אל תייחס אשמה לילד, שקול פנייה לגורם בבית הספר.
- תוקף: בלי הענשה מיידית — עזור לילד להבין את ההשפעה על הצד השני, עודד תיקון.
- צופה מהצד: עודד את הילד לא להישאר אדיש ולתמוך בנפגע.
- נחשף (דיסאינפורמציה): הסבר שהתוכן כוזב/מזויף, למד זיהוי מקורות וחשיבה ביקורתית, בלי לבייש.

מקרים חמורים (הטרדה מינית/סחיטה, הפצת עירום, איום פיזי, אובדנות): המלץ מפורשות
לתעד ראיות ולפנות למשטרה (100) ול-105; באובדנות הוסף ער"ן 1201 ומצב חירום 101.

בלי ז'רגון מקצועי, בלי רשימות, בלי הקדמות. רק ההמלצה עצמה."""

# Templated fall-backs by role (used when LLM unavailable).
_FALLBACK = {
    "victim": "הילד שלך היה קורבן. שוחח איתו בנחת, שאל איך הרגיש, והבהר שזו לא אשמתו. שקול פנייה למחנכת.",
    "aggressor": "הילד שלך פגע באחר. שוחח בלי להאשים, עזור לו להבין את ההשפעה על הצד השני, ועודד תיקון.",
    "bystander": "הילד שלך נכח באירוע פגיעה. שאל מה ראה, הסבר שאדישות מזיקה, ועודד אותו לתמוך בנפגע.",
    "exposed": "הילד שלך נחשף לתוכן כוזב/מזויף והאמין לו. הראה לו איך מזהים מקור לא אמין, ועודד בדיקת עובדות לפני שיתוף, בלי לבייש.",
    "none": "זוהה אירוע בעייתי. מומלץ לעקוב ולשוחח עם הילד על מה שקורה בקבוצה.",
}

_POLICE_SUFFIX = (
    " זהו אירוע חמור שעלול להיות פלילי — תעדו ראיות (צילומי מסך), אל תפיצו הלאה, "
    "ופנו למשטרה (100) ול-105 (המטה הלאומי להגנה על ילדים ברשת)."
)
_SELF_HARM_SUFFIX = (
    " אל תשאירו את הילד לבד. פנו מיידית לעזרה: ער\"ן 1201, או 101/100 במצב חירום, "
    "ותאמו עם גורם טיפולי בהקדם."
)


def generate_recommendation(analysis: AnalysisResult, message: IncomingMessage) -> str:
    """Always returns a non-empty string. Never raises."""
    try:
        base = _llm_recommendation(analysis, message)
    except Exception as exc:  # noqa: BLE001
        print(f"[reco] LLM failed, using template: {exc}")
        base = _FALLBACK.get(analysis.role_of_child, _FALLBACK["none"])
        # Escalate severe cases even on the fallback path. The analyzer does not set
        # analysis.escalation (it stays "none"), so derive it from category + severity
        # using the same rule the backend applies when building the alert — otherwise
        # sexual/nudity/high-threat events lose their police instruction here.
        severity = severity_from_score(analysis.toxicity_score)
        escalation = analysis.escalation if analysis.escalation != "none" \
            else escalation_from(analysis.category, severity)
        if analysis.category == "self_harm":
            base += _SELF_HARM_SUFFIX
        elif escalation == "police":
            base += _POLICE_SUFFIX
    return base


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
