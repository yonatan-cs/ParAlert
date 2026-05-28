"""
Manual analyzer test cases for Dev 1.

Run from the project root:
    .\\.venv\\Scripts\\python.exe .\\ml_service\\test_analyzer_cases.py

The output is intentionally compact:
    case name | level | score | toxic/not toxic | category
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import IncomingMessage  # noqa: E402
from ml_service.analyzer import ToxicityAnalyzer  # noqa: E402


def _message(
    *,
    case_id: str,
    text: str,
    sender_id: str = "dani_2",
    child_id: str = "yonatan_1",
    context_before: list[str] | None = None,
    context_after: list[str] | None = None,
) -> IncomingMessage:
    return IncomingMessage(
        message_id=case_id,
        group_name="כיתה ו'2 - בדיקות",
        sender_id=sender_id,
        sender_name="דני" if sender_id != child_id else "יונתן",
        child_id=child_id,
        text=text,
        media_url=None,
        timestamp=datetime.now(),
        context_before=context_before or [],
        context_after=context_after or [],
    )


def _level(explanation: str) -> str:
    return explanation.split(":", 1)[0]


def main() -> None:
    analyzer = ToxicityAnalyzer(use_model=True)

    cases = [
        (
            "clean_homework_coordination",
            _message(
                case_id="case_001",
                text="אני יכול להכין את השקופית הראשונה אם זה עוזר.",
                context_before=[
                    "מתי נפגשים לעבוד על המצגת?",
                    "אפשר בארבע בספרייה.",
                ],
                context_after=[
                    "מעולה, אני אכין את הסיכום.",
                    "נחלק תפקידים לכולם.",
                ],
            ),
        ),
        (
            "clean_disagreement",
            _message(
                case_id="case_002",
                text="אני לא מסכים עם הרעיון הזה, אולי נבחר כיוון אחר.",
                context_before=[
                    "בואו נעשה את המצגת על חלל.",
                    "אני דווקא מעדיף על אנרגיה.",
                ],
                context_after=[
                    "אפשר להצביע.",
                    "כן, בלי לריב.",
                ],
            ),
        ),
        (
            "direct_profanity",
            _message(
                case_id="case_003",
                text="איזה אפס אתה, אף אחד לא צריך אותך פה.",
            ),
        ),
        (
            "mild_insult",
            _message(
                case_id="case_004",
                text="אתה ממש מעצבן היום, תפסיק להציק.",
                context_before=["די, כולם מדברים ביחד."],
                context_after=["בואו נירגע רגע."],
            ),
        ),
        (
            "single_exclusion_phrase",
            _message(
                case_id="case_005",
                text="אל תבוא לחזרה מחר, אנחנו נסתדר לבד.",
                context_before=[
                    "מחר עושים חזרה למצגת.",
                    "מי מגיע?",
                ],
            ),
        ),
        (
            "contextual_boycott_no_curses",
            _message(
                case_id="case_006",
                text="כולם מעדיפים שתישאר בבית מחר.",
                context_before=[
                    "פתחנו קבוצה נפרדת כדי לסיים את העבודה.",
                    "עדיף שזה יהיה בלי יונתן.",
                    "לא צריך לשתף אותו בכל דבר.",
                    "אם הוא יבוא זה רק יפריע.",
                ],
                context_after=[
                    "אל תכתוב בקבוצה השנייה.",
                    "אנחנו כבר החלטנו מי מציג.",
                    "זה לא אישי, פשוט יותר קל בלעדיך.",
                    "יונתן: אז אתם מוציאים אותי מהקבוצה?",
                ],
            ),
        ),
        (
            "repeated_social_exclusion",
            _message(
                case_id="case_007",
                text="לא מזמינים אותך, תבין את הרמז.",
                context_before=[
                    "מי בא לפארק אחרי הלימודים?",
                    "כולם חוץ מיונתן.",
                    "כבר אמרנו לו שלא יבוא.",
                ],
                context_after=[
                    "אף אחד לא רוצה אותו שם.",
                    "שלא יעשה מזה סיפור.",
                ],
            ),
        ),
        (
            "threat_if_tells_teacher",
            _message(
                case_id="case_008",
                text="אם תספר למורה אני מחכה לך אחרי בית ספר.",
                context_before=[
                    "די, זה לא בסדר שאתם מוציאים אותו.",
                    "אני אומר את זה למחנכת.",
                ],
            ),
        ),
        (
            "bystander_like_context",
            _message(
                case_id="case_009",
                text="אל תזמינו את רועי, הוא רק הורס.",
                sender_id="dani_2",
                child_id="yonatan_1",
                context_before=[
                    "יונתן רק קורא את ההודעות ולא משתתף.",
                    "מדברים עכשיו על רועי.",
                ],
                context_after=[
                    "נפתח קבוצה בלי רועי.",
                    "יונתן: אולי לא כדאי לדבר עליו ככה.",
                ],
            ),
        ),
        (
            "child_as_aggressor",
            _message(
                case_id="case_010",
                text="אל תבואו אליו, אף אחד לא רוצה אותו בקבוצה.",
                sender_id="yonatan_1",
                child_id="yonatan_1",
                context_before=[
                    "מי מזמין את רועי לעבודה?",
                    "אולי נצרף אותו.",
                ],
            ),
        ),
        (
            "sarcastic_but_not_bullying",
            _message(
                case_id="case_011",
                text="יופי גאון, שכחת שוב את הקובץ, אבל לא נורא נתקן ביחד.",
                context_before=[
                    "אוי לא, שלחתי את הגרסה הלא נכונה.",
                ],
                context_after=[
                    "חח הכל טוב, קורה.",
                    "אני אעלה עכשיו את הקובץ הנכון.",
                ],
            ),
        ),
        (
            "pressure_without_direct_phrase",
            _message(
                case_id="case_012",
                text="אולי עדיף שלא תציג הפעם, זה יהיה יותר טוב לכולם.",
                context_before=[
                    "יונתן רוצה להציג את החלק שלו.",
                    "בפעם הקודמת צחקו עליו.",
                    "בואו נחסוך את זה.",
                ],
                context_after=[
                    "כן, שמישהו אחר ידבר במקומו.",
                    "הוא יכול רק לשלוח את הסיכום.",
                ],
            ),
        ),
        (
            "severe_profanity_and_exclusion",
            _message(
                case_id="case_013",
                text="אתה מטומטם, אל תבוא יותר, אף אחד לא רוצה אותך.",
                context_before=[
                    "תפסיקו לרדת עליו.",
                ],
            ),
        ),
        (
            "normal_invitation_with_do_not_come_to_wrong_place",
            _message(
                case_id="case_014",
                text="אל תבוא לספרייה, בסוף נפגשים בכיתה.",
                context_before=[
                    "איפה נפגשים לחזרה?",
                    "חשבתי שבספרייה.",
                ],
                context_after=[
                    "כולם מוזמנים לכיתה בשעה ארבע.",
                    "יונתן תביא את המחשב שלך.",
                ],
            ),
        ),
    ]

    print(f"model_used={analyzer.model_name}")
    print("case | level | score | toxic | category")
    print("-" * 72)
    for name, message in cases:
        result = analyzer.analyze(message)
        print(
            f"{name} | {_level(result.explanation)} | "
            f"{result.toxicity_score:.3f} | {result.is_toxic} | {result.category}"
        )


if __name__ == "__main__":
    main()
