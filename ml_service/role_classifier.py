"""
Role classifier — who is aggressor / victim / bystander. OWNER: ML Dev 2.

Separate file so two ML devs never touch the same code:
  - analyzer.py      (ML Dev 1) = toxicity scoring + orchestration
  - role_classifier.py (ML Dev 2) = role + category logic

analyzer.py imports classify_role() / classify_category() from here.
Keep the signatures stable — that's the internal contract between the two ML devs.
"""
from __future__ import annotations

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import IncomingMessage, Role, Category  # noqa: E402

# TODO ML Dev 2: replace these heuristics with a real classifier
# (DictaBERT head, few-shot LLM, or rules tuned on the conversation datasets).
_SELF_HARM = [
    "בא לי למות", "רוצה למות", "לא רוצה לחיות", "אין לי כוח לחיות",
    "נמאס לי לחיות", "אין טעם לחיות", "לשים סוף", "לפגוע בעצמי",
    "להרוג את עצמי", "אני אתאבד", "אתאבד", "אין לי סיבה לחיות",
    "want to die", "kill myself", "end it all", "no reason to live",
    "i want to die", "hurt myself", "cut myself", "suicidal",
]
_THREAT = ["מחכה לך", "תמות", "אני אחכה", "תיזהר",
           "i'll be waiting", "you're dead", "watch your back", "i'll get you"]
_EXCLUSION = ["לא מזמינים", "כולם נגדך", "אל תבוא", "אף אחד לא רוצה",
              "nobody wants you", "not invited", "go away", "no one likes you"]


def classify_category(text: str) -> Category:
    low = text.lower()  # case-insensitive (English); Hebrew unaffected
    if any(w in low for w in _SELF_HARM):
        return "self_harm"
    if any(w in low for w in _THREAT):
        return "threat"
    if any(w in low for w in _EXCLUSION):
        return "exclusion"
    return "harassment"


def classify_role(message: IncomingMessage, is_toxic: bool) -> Role:
    """Decide the child's role in this toxic event.

    Current rule: child sent it -> aggressor, else victim.
    TODO ML Dev 2: bystander detection (toxic msg between two OTHERS, child only present).
    """
    if not is_toxic:
        return "none"
    if any(w in message.text.lower() for w in _SELF_HARM):
        return "victim"  # a child in distress is a victim, never the "aggressor"
    return "aggressor" if message.sender_id == message.child_id else "victim"
