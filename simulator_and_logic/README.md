# simulator_and_logic/ — סימולטור דאטה + מנוע המלצות (Dev 4)

שני רכיבים מנותקים: וואטסאפ מזויף שמזרים שיחות, ומנוע ההמלצות (ה-killer feature).

## הרצה
```bash
cd simulator_and_logic
pip install -r requirements.txt

# 1) מנוע ההמלצות (בדיקה עצמאית)
export ANTHROPIC_API_KEY=...        # בלי המפתח → נופל ל-template, עדיין עובד
python recommendation_engine.py

# 2) סימולטור (הבקאנד חייב לרוץ על :8000)
python simulator.py
python simulator.py --conversation conversations/escalation_demo.json --speed 0.5
```

## רכיבים
| קובץ | תפקיד |
|------|-------|
| `simulator.py` | Client HTTP — שולח כל הודעה כחוזה A ל-`POST /ingest` עם חלון קונטקסט |
| `recommendation_engine.py` | `generate_recommendation(analysis, message) -> str` — black box לבקאנד |
| `conversations/*.json` | תסריטי שיחה מדומים (רגיל → הסלמה לחרם/איום) |

## משימות
- [ ] להוסיף עוד תסריטים: צופה מהצד, הילד כתוקף, שיחה רגילה לגמרי (false-positive check)
- [ ] לכוונן את `SYSTEM_PROMPT` להמלצות אמפתיות יותר
- [ ] (אופ') הזרמה אקראית בקצב משתנה לדמו חי

## הערות
- `generate_recommendation` תמיד מחזיר טקסט (LLM → אחרת template). הדמו לא מציג תיבה ריקה.
- כדי להוסיף שיחה: קובץ JSON חדש ב-`conversations/` במבנה של `escalation_demo.json`.
