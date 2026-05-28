# 🛡️ SafeNet

מערכת התראות למניעת בריונות ברשת, בדגש על וואטסאפ. ההורה מקבל התראה בזמן אמת עם
ההודעה הבעייתית + קונטקסט, ציון רעילות, פרטים מזהים, והמלצה לפעולה.

📄 **התכנית המלאה, החוזים וחלוקת העבודה:** [`Idea+Plan.md`](./Idea+Plan.md)

## ארכיטקטורה
```
  Simulator (Dev4) --POST /ingest--> Backend (Dev2) --analyze--> ML (Dev1)
                                          |  --recommend--> LLM engine (Dev4)
                                          |  --save--> SQLite
  Dashboard (Dev3) <--GET /alerts------- Backend
```
תקשורת אך ורק דרך החוזים ב-[`contracts/`](./contracts/). אף מודול לא נוגע בקוד של אחר.

## מבנה
| תיקייה | בעלים | תפקיד |
|--------|-------|-------|
| `contracts/` | כולם | מודלי הנתונים המשותפים (מקור אמת) |
| `ml_service/` | Dev 1 | מנוע זיהוי רעילות (HuggingFace) |
| `backend_api/` | Dev 2 | FastAPI — ליבה, DB, ניתוב |
| `frontend_dashboard/` | Dev 3 | דשבורד ההורה (React / fallback HTML) |
| `simulator_and_logic/` | Dev 4 | וואטסאפ מזויף + מנוע המלצות LLM |

## Quickstart (הדמו המלא)
```bash
# טרמינל 1 — בקאנד
cd backend_api && pip install -r requirements.txt && uvicorn main:app --port 8000

# טרמינל 2 — סימולטור
cd simulator_and_logic && pip install -r requirements.txt && python simulator.py

# דשבורד — פתח frontend_dashboard/demo.html בדפדפן
```
ה-pipeline עובד מקצה לקצה גם בלי מודל HF ובלי מפתח LLM (fallbacks מובנים) — הדמו לא קורס.

## בראנצ'ים
`dev1-ml` · `dev2-backend` · `dev3-frontend` · `dev4-sim` — מיזוג ל-`main` רק כשעובד מקצה לקצה.
