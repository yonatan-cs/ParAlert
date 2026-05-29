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
    # Hebrew insults / put-downs
    "אפס", "מטומטם", "מטומטמת", "טמבל", "טמבלית", "שמן", "שמנה", "מכוער",
    "מכוערת", "דביל", "דבילית", "תמות", "מעצבן", "מעצבנת", "לך מפה", "סתום",
    "סתמי את הפה", "חנון", "חנונית", "לוזר", "לוזרית", "נכה", "מוזר", "מוזרה",
    "דוחה", "דוחה אותך", "מגעיל", "מגעילה", "פתטי", "פתטית", "כושל", "כישלון",
    "בכיין", "בכיינית", "תינוק", "תינוקת", "פחדן", "פחדנית", "אידיוט", "אידיוטית",
    "בהמה", "חמור", "חרא של בנאדם", "שום דבר", "אתה כלום", "את כלום", "מסכן",
    "מסכנה", "עלוב", "עלובה", "בוגד", "בוגדת", "מטונף", "מטונפת", "טיפש", "טיפשה",
    "אין לך חברים", "מי בכלל מדבר איתך", "כולם צוחקים עליך", "בושה",
    # English (matched case-insensitively) so the fallback isn't blind to English.
    "idiot", "stupid", "loser", "ugly", "dumb", "moron", "retard", "retarded",
    "freak", "weirdo", "creep", "nerd", "geek", "fatty", "fatso",
    "disgusting", "gross", "lame", "useless", "pathetic", "worthless", "trash",
    "garbage", "clown", "joke", "embarrassing", "loser", "failure", "nobody",
    "shut up", "shut your mouth", "kill yourself", "kys", "go kill yourself",
    "nobody likes you", "nobody cares", "no one cares about you", "no friends",
    "you have no friends", "hate you", "i hate you", "everyone hates you",
    "you suck", "you're nothing", "youre nothing", "go die", "drop dead",
    "waste of space", "waste of air", "cringe", "ratio", "skill issue",
    "coward", "crybaby", "baby", "snitch",
    # Profanity (he + en)
    "חרא", "זבל", "מפגר", "מפגרת", "מניאק", "מניאקית", "שרמוטה", "בן זונה",
    "בת זונה", "לך תזדיין", "תזדיין", "תזדייני", "מזדיין",
    "חתיכת חרא", "חתיכת זבל", "אמא שלך", "די כבר", "סקס",
    "shit", "shitty", "fuck", "fucking", "fuck you", "fuck off", "asshole",
    "bitch", "bastard", "dick", "dickhead", "douche", "douchebag", "slut",
    "whore", "cunt", "prick", "piss off", "stfu", "gtfo", "wtf", "screw you",
    "son of a bitch", "motherfucker", "jackass", "dumbass", "dipshit",
]

_EXCLUSION_PHRASES = [
    "אל תבוא", "אל תבואי", "אל תזמינו", "אל תזמינו אותו", "אל תזמינו אותה",
    "לא צריך שתבוא", "לא צריך שתבואי", "תישאר בבית", "תישארי בבית",
    "אף אחד לא רוצה אותך", "אף אחד לא רוצה אותה", "כולם מעדיפים", "כולם חוץ",
    "כולם חוץ ממך", "כולם נגדך", "לא מזמינים", "לא מזמינים אותך", "בלי יונתן",
    "בלי רועי", "קבוצה נפרדת", "קבוצה שנייה", "קבוצה בלי", "נפתח קבוצה בלי",
    "פותחים קבוצה בלי", "הוצאנו אותך", "הוצאנו אותו", "הוצאנו אותה",
    "לא עובד איתו", "לא עובדים איתו", "לא עובדים איתך", "שלא יבוא", "שלא תבוא",
    "לא לשתף אותך", "לא משתפים אותך", "מוציאים אותי מהקבוצה", "מוציאים אותך",
    "זה חרם", "עושים עליו חרם", "עושים עליך חרם", "החרמנו אותך", "מחרימים אותך",
    "עדיף שלא תציג", "יותר טוב לכולם", "יהיה יותר טוב בלעדיך", "בלעדיך יהיה כיף",
    "מישהו אחר ידבר במקומו", "רק לשלוח את הסיכום", "אתה לא חלק מהקבוצה",
    "את לא שייכת לפה", "אתה לא שייך לפה", "אף אחד לא רוצה לשבת לידך",
    "אל תשב איתנו", "אל תשבי איתנו", "תמצא חברים אחרים", "לך לקבוצה אחרת",
    # English
    "nobody wants you", "no one wants you", "don't come", "dont come",
    "you're not invited", "youre not invited", "not invited", "uninvited",
    "everyone is against you", "everyone's against you", "everyone hates you",
    "go away", "get out", "without you", "no one likes you", "leave the group",
    "leave the chat", "get out of the group", "you're not welcome",
    "youre not welcome", "you don't belong here", "you dont belong",
    "find other friends", "sit somewhere else", "don't sit with us",
    "we made a group without you", "you're excluded", "youre excluded",
    "no one wants to sit with you", "everyone but you",
]

_THREAT_PHRASES = [
    "אני מחכה לך", "אנחנו מחכים לך", "אחרי בית ספר", "אחרי הלימודים",
    "תיזהר", "תיזהרי", "תיזהר ממני", "אם תספר", "אם תספרי", "אם תלשין",
    "תמות", "אני אהרוג אותך", "אני אחסל אותך", "אני אשבור לך", "אני ארביץ לך",
    "תקבל מכות", "תחטוף", "תחטוף ממני", "אתה גמור", "את גמורה", "תשלם על זה",
    "אני אמצא אותך", "אני יודע איפה אתה גר", "אני יודע איפה את גרה",
    "בוא נצא בחוץ", "חכה שתצא", "אל תעז לבוא", "תתחבא טוב", "תספור את הימים",
    "אני אדאג שתצטער", "אתה תצטער", "את תצטערי", "תבכה אצלי", "יהיה לך רע",
    # English
    "i'll be waiting", "ill be waiting", "we're waiting for you", "after school",
    "you're dead", "youre dead", "you are dead", "watch your back",
    "i'll get you", "ill get you", "i will find you", "i'll find you",
    "i'll hurt you", "ill hurt you", "i'll kill you", "ill kill you",
    "i'll beat you", "you're gonna get it", "youre gonna get it",
    "you'll regret this", "youll regret this", "you'll pay for this",
    "i know where you live", "you better watch out", "i'm coming for you",
    "im coming for you", "count your days", "wait till you get out",
    "you're finished", "youre finished", "make you regret",
]

# Self-harm / suicidal ideation — a distress signal, NOT toxicity, so a profanity/
# toxicity model misses it; explicit phrasing is the right detector. Always severe.
_SELF_HARM_PHRASES = [
    "בא לי למות", "רוצה למות", "אני רוצה למות", "לא רוצה לחיות",
    "אין לי כוח לחיות", "אין לי כוח יותר", "נמאס לי לחיות", "נמאס לי מהחיים",
    "אין טעם לחיות", "אין לי טעם", "לשים סוף", "לשים סוף לחיים שלי",
    "לפגוע בעצמי", "פגעתי בעצמי", "חתכתי את עצמי", "אני חותך את עצמי",
    "להרוג את עצמי", "אני אתאבד", "אתאבד", "אני רוצה להתאבד", "מתאבד",
    "אין לי סיבה לחיות", "עדיף שלא אהיה פה", "כולם יהיו יותר טוב בלעדיי",
    "אני לא רוצה להיות פה יותר", "אני שונא את עצמי", "אני שונאת את עצמי",
    "אני רוצה להיעלם", "החיים שלי נגמרו", "אני לא שווה כלום", "כואב לי לחיות",
    "want to die", "i want to die", "wanna die", "kill myself",
    "i want to kill myself", "i'm going to kill myself", "end it all",
    "end my life", "no reason to live", "nothing to live for",
    "hurt myself", "i hurt myself", "cut myself", "cutting myself", "self harm",
    "suicidal", "i'm suicidal", "want to disappear", "wish i was dead",
    "i wish i were dead", "better off without me", "everyone better off without me",
    "i hate myself", "can't go on", "cant go on", "i give up on life",
    "i don't want to be here", "i dont want to be here anymore",
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
        low = text.lower()  # case-insensitive matching for English; Hebrew is unaffected
        hits = sum(1 for phrase in _TOXIC_KEYWORDS if phrase in low)
        exclusion_hits = sum(1 for phrase in _EXCLUSION_PHRASES if phrase in low)
        threat_hits = sum(1 for phrase in _THREAT_PHRASES if phrase in low)
        self_harm_hits = sum(1 for phrase in _SELF_HARM_PHRASES if phrase in low)
        safe_context_hits = sum(1 for phrase in _SAFE_CONTEXT_PHRASES if phrase in low)

        # Example: "don't come to the library, we meet in class" is logistical,
        # not bullying. These guards reduce that false positive.
        if exclusion_hits == 1 and safe_context_hits >= 2 and not hits and not threat_hits:
            exclusion_hits = 0
        if safe_context_hits >= 2 and not threat_hits:
            hits -= sum(1 for phrase in _AMBIGUOUS_LOGISTICS_PHRASES if phrase in low)
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
        if self_harm_hits:
            scores.append(0.95)  # self-harm / suicidal ideation -> always severe

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
