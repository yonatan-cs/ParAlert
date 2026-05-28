# 🛡️ SafeNet

מערכת התראות למניעת בריונות ברשת, בדגש על וואטסאפ. ההורה מקבל התראה בזמן אמת עם
ההודעה הבעייתית + קונטקסט, ציון רעילות, פרטים מזהים, והמלצה לפעולה.

📄 **התכנית המלאה, החוזים וחלוקת העבודה:** [`Idea+Plan.md`](./Idea+Plan.md)

## ארכיטקטורה
```
  WhatsApp Bridge ⭐ ─┐
  (whatsapp-web.js)   │ POST /ingest (חוזה A)
  Simulator (fallback)┤
                      ▼
                  Backend ──analyze──► ML
                      │  ──recommend──► LLM engine
                      │  ──save──► SQLite
  Dashboard ◄──GET /alerts── Backend
```
שני מקורות, אותו חוזה A — הבקאנד אדיש למקור. תקשורת רק דרך [`contracts/`](./contracts/).

## מבנה
| תיקייה | בעלים | תפקיד |
|--------|-------|-------|
| `contracts/` | כולם | מודלי הנתונים המשותפים (מקור אמת) |
| `ml_service/` | זוג ML | זיהוי רעילות + תפקיד (HuggingFace) |
| `backend_api/` | זוג Fullstack | FastAPI — ליבה, DB, ניתוב |
| `frontend_dashboard/` | זוג Fullstack | דשבורד ההורה (React / fallback HTML) |
| `whatsapp_bridge/` ⭐ | זוג Fullstack | אינטגרציה אמיתית לוואטסאפ (Node, QR) — דרישת השופט |
| `simulator_and_logic/` | זוג Fullstack | סימולטור fallback + מנוע המלצות LLM |

חלוקת עבודה מלאה: [`WORKPLAN.md`](./WORKPLAN.md)

## Quickstart (הדמו המלא)
```bash
# טרמינל 1 — בקאנד
cd backend_api && pip install -r requirements.txt && uvicorn main:app --port 8000

# טרמינל 2 — מקור דאטה: אמיתי (וואטסאפ) או fallback (סימולטור)
cd whatsapp_bridge && npm install && node index.js     # סרוק QR ממספר burner ⭐
# או:
cd simulator_and_logic && pip install -r requirements.txt && python simulator.py

# טרמינל 3 — דשבורד (React + Vite)
cd frontend_dashboard/app && npm install && npm run dev
```
ה-pipeline עובד מקצה לקצה גם בלי מודל HF ובלי מפתח LLM (fallbacks מובנים) — הדמו לא קורס.

## חי (פרוס)
- 🖥️ דשבורד: <https://hackathon-project-tau-seven.vercel.app> — Vercel, ענף `main`
- ⚙️ בקאנד: <https://safenet-backend-cnmy.onrender.com> — Render, ענף `fs-server`

הכל ממוזג ל-`main`: ML + בקאנד + פרונט + סימולטור + חוזי v2 (התראת בריונות **ו**דיסאינפורמציה,
הסלמה למשטרה, מדד אמינות, מדיה). הענפים הישנים (`fs-server`/`fs-dashboard`/`fullstack`/`ml`)
נשמרים ב-origin בלבד. הרצת מודלים אמיתיים למצגת: ראה [`DEPLOY.md`](./DEPLOY.md) (Cloudflare Tunnel).
