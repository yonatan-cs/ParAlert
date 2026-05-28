# frontend_dashboard/ — דשבורד ההורה (Dev 3)

החזית של המוצר — מה שהשופטים רואים. עובד מול `GET /alerts` (חוזה C) או מול `mock_data.json`.

## אופציה A — fallback מיידי (אפס build)
פתח את `demo.html` בדפדפן. מושך מ-`localhost:8000/alerts`, ואם אין שרת — נופל ל-`mock_data.json`.
**רשת ביטחון:** תמיד יש דמו עובד. בנה את אפליקציית React לצידו.

## אופציה B — React + Vite + Tailwind (המוצר האמיתי) — כבר בנוי ב-`app/`
```bash
cd frontend_dashboard/app
npm install
npm run dev      # http://localhost:5173
npm run build    # בדיקת קומפילציה (dist/)
```
מושך מ-`http://localhost:8000/alerts`; אם אין שרת → fallback ל-`public/mock_data.json`. Polling כל 3 שניות.
**זמן אמת:** מתחבר ל-`ws://localhost:8000/ws/alerts` (WebSocket של FS-A) לדחיפת התראות מיידית; ה-polling נשאר רשת ביטחון אם ה-socket נכשל.

### מבנה `app/`
| קובץ | תפקיד |
|------|-------|
| `src/App.jsx` | טאבים (צ'אט/דשבורד) + polling + מצב חיבור + מיון + highlight להתראה חדשה |
| `src/components/ChatSimulator.jsx` | פתיחת הדמו — צ'אט קבוצתי בסגנון וואטסאפ שמתדרדר לחרם + banner התראה |
| `src/components/SummaryBar.jsx` | פירוק ל-3 זוויות (קורבן/תוקף/צופה) |
| `src/components/FilterBar.jsx` | סינון לפי תפקיד הילד |
| `src/components/AlertCard.jsx` | כרטיס לפי חוזה C: חומרה, זמן, מד רעילות, בועות, המלצה |
| `src/lib/format.js` | מפות עברית (קטגוריה/תפקיד/חומרה) + זמן יחסי |
| `src/data/demoChat.js` | תסריט הצ'אט לפתיחת הדמו |
| `src/index.css` | Tailwind v4 (`@import "tailwindcss"`) + אנימציית כניסה |
| `public/mock_data.json` | fallback (עותק מ-`contracts/mock_alerts.json`) |

**זרימת דמו:** טאב "צ'אט הילד" → ▶ הפעל → שיחה מתדרדרת + banner "התראה נשלחה" → עבור לטאב "דשבורד הורה" לראות את ההתראה.

Tailwind v4 דרך `@tailwindcss/vite` (ב-`vite.config.js`). RTL מוגדר ב-`index.html` (`dir="rtl"`).

## מה לבנות (חוזה C)
- כרטיס התראה: שם קבוצה + תפקיד הילד (קורבן/תוקף/צופה)
- **מד רעילות ויזואלי** (`toxicity_score` 0–1) + צבע severity
- בועות צ'אט: `context_before` → `trigger_message` (מודגש) → `context_after`
- **"המלצה לפעולה"** בולטת (`recommendation`)
- ריענון/realtime (polling כל כמה שניות, או WebSocket אם Dev 2 מוסיף)

## משימות
- [ ] להקים React+Vite+Tailwind+shadcn/ui
- [ ] קומפוננטת `AlertCard` לפי חוזה C
- [ ] מסך "שיחת קבוצה חיה" (אופ', לפתיחת הדמו)
- [ ] אנימציה כשהתראה חדשה קופצת

## הערות
- `mock_data.json` = עותק מ-`contracts/mock_alerts.json`. אם החוזה משתנה — לרענן.
- CORS כבר פתוח בבקאנד (`allow_origins=["*"]`).
