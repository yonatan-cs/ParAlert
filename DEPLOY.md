# 🚀 DEPLOY — SafeNet חי לשופטים

> המטרה: לא הדגמה — **מוצר עובד, פרוס, end-to-end**. שופט נכנס מהטלפון שלו לקישור Vercel,
> רואה דשבורד אמיתי, ורואה התראה נכנסת בזמן אמת. זה מה שמנצח.

## תזת הניצחון
1. **זה באמת עובד** — frontend פרוס ב-Vercel מדבר עם backend חי; הודעת וואטסאפ אמיתית (מ-burner) → התראה בדשבורד.
2. **חשיבה מוצרית כנה** — אנחנו יודעים שהמוצר האמיתי = אפליקציית-לוויין על מכשיר הילד (ראה למטה). לא מתחזים.
3. **ליטוש** — UI נקי, אנימציות, מסך הגדרות, המלצת פעולה אמפתית (ה-killer feature).

## ארכיטקטורה פרוסה
```
  Vercel (frontend, static)  ──https GET /alerts──►  Backend (host מתמשך)
        ▲  └──────────────────wss /ws/alerts────────►   (Render/Railway/Fly)
        │                                                     ▲
   judge phone                          WhatsApp burner ──POST /ingest── bridge (worker)
```
Vercel = רק frontend. Backend + bridge חייבים host עם **תהליך רץ-תמיד** (לא serverless).

---

## 👤 FS-A — מה צריך לעשות (backend + bridge), לפי עדיפות

### 1. לפרוס את ה-backend ל-host מתמשך (Render / Railway / Fly)
- [ ] Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] תלויות מ-`backend_api/requirements.txt`
- [ ] **CORS**: לקרוא origins מ-env (להוסיף ב-`main.py`: `CORS_ORIGINS` מופרד בפסיקים, ברירת מחדל `*` לדמו). להתיר את דומיין ה-Vercel.
- [ ] DB: SQLite על disk מתמשך (Render Disk) — או לקבל ephemeral לדמו (לתעד).
- [ ] לוודא `GET https://<backend>/health` מחזיר (כולל USE_MODEL/ALERT_THRESHOLD).
- [ ] **WebSocket**: לוודא ש-`wss://<backend>/ws/alerts` עובד דרך ה-proxy של ה-host (Render/Railway תומכים).

### 2. לפרוס את ה-bridge כ-worker מתמשך ⭐
- [ ] host שמריץ תהליך ארוך + Chromium: Render **Background Worker** / VPS קטן / Railway service. (Fallback קביל: להריץ את ה-bridge ממחשב נייד שמצביע ל-backend הפרוס.)
- [ ] env: `BACKEND_URL=https://<backend>/ingest`
- [ ] לסרוק QR פעם אחת ממספר **burner** (צריך גישה ללוגים בשביל ה-QR).
- [ ] זרימה חיה: הודעת וואטסאפ אמיתית → backend פרוס → דחיפה ל-dashboard הפרוס.

### 3. לזרוע את הדשבורד החי כדי שלא יהיה ריק לשופטים
- [ ] להוסיף route `POST /demo/seed` שמכניס את ההתראות לדוגמה (מ-`contracts/mock_alerts.json`) → הדשבורד הפרוס מציג תוכן אמיתי-למראה מיד, בלי צורך לסרוק וואטסאפ.
- [ ] חלופה: להריץ `simulator.py` (יש בו כבר `--dry-run`) מול ה-`/ingest` הפרוס.

### 4. למסור ל-FS-B את כתובת ה-backend הציבורית
- [ ] `https://<backend>` → FS-B מזין ל-Vercel כ-`VITE_API_BASE` (ה-wss נגזר אוטומטית).

### 5. כשזוג ML ממזג
- [ ] `USE_MODEL=true` → מעבר מ-keyword-fallback למודל האמיתי.

---

## 👤 FS-B — סטטוס (מוכן) + צעדי Vercel
**מוכן ואומת:** `engines.node=20.x`, env-driven (`VITE_API_BASE`, WS נגזר), fallback ל-mock כשאין backend → אף פעם לא ריק. build הורץ והוגש מקומית כמו Vercel.

> **תיקון 404 NOT_FOUND:** האפליקציה ב-subdir. חובה להגדיר **Root Directory** ל-`frontend_dashboard/app` — אחרת Vercel בונה מהשורש, לא מוצא output, ומחזיר 404. ה-`vercel.json` יושב בתוך תיקיית האפליקציה (SPA rewrites).

**פרויקט חדש:**
1. vercel.com → Add New → Project → Import `Hackathon-Project`.
2. **Root Directory → `frontend_dashboard/app`** (לחצן Edit ליד Root Directory). Framework זוהה אוטומטית: **Vite**.
3. Production Branch: `fullstack` (Settings → Git), או `main` אחרי מיזוג.
4. Environment Variables → `VITE_API_BASE=https://<backend מ-FS-A>` (בלי זה → mode הדגמה/mock).
5. Deploy.

**פרויקט קיים שנתן 404:**
- Settings → Build & Deployment → **Root Directory** = `frontend_dashboard/app` → Save → Deployments → Redeploy.

> חלופה ב-CLI מתוך התיקייה: `cd frontend_dashboard/app && npx vercel` (הריצו בעצמכם עם `! ...`).

## אינטגרציה (הצעד שמחבר הכל)
- למזג `fs-server` + `fs-dashboard` → `fullstack` → `main` לפני הפריסה הסופית.
- ה-wiring היחיד: `VITE_API_BASE` (Vercel) → backend; CORS ב-backend מתיר את דומיין ה-Vercel.

---

## תכנית הדמו (3 מערכות)
1. **טלפון הילד:** קבוצת וואטסאפ מתדרדרת לחרם (bridge חי, או טאב "צ'אט הילד").
2. **טלפון ההורה (קישור Vercel, על הטלפון של השופט):** ההתראה קופצת בזמן אמת (WS) — חומרה, זווית, קונטקסט.
3. **ה-killer:** המלצת הפעולה האמפתית (ספציפית לתפקיד). אז מסך ההגדרות (רגישות, קבוצות) = מוצר אמיתי.
4. **סגירה:** החזון הכן — production = אפליקציית-לוויין; היום הוכחנו שהליבה עובדת, פרוסה, חיה.

## חזון המוצר (כנות מנצחת אצל שופטים)
אין API רשמי לקרוא קבוצות וואטסאפ של משתמש (E2E + פרטיות). מוצר תקין אמיתי =
**אפליקציית-לוויין על מכשיר הילד** (אנדרואיד `NotificationListenerService`, ניתוח on-device,
שולח להורה רק התראות, בהסכמה). ה-bridge המתארח = הוכחת-היתכנות של ליבת הזיהוי+התראה.

## סיכונים ו-fallbacks
- וואטסאפ מקרטע על הבמה → טאב "צ'אט הילד" + `simulator.py` נותנים את אותו זרימה.
- backend לא עולה → frontend נופל ל-mock, עדיין interactive.
- LLM/מודל נופלים → template/keyword fallback, אף פעם לא תיבה ריקה.

## סטטוס חי (אומת מול הפרודקשן)
- ✅ frontend (Vercel) מחובר ל-backend (Render) — ה-URL baked, CORS `*`, מושך `/alerts` אמיתי.
- ✅ WebSocket `wss://.../ws/alerts` עובד דרך Render (push בזמן אמת אומת).
- ✅ `/alerts` מאוכלס דרך הצינור האמיתי (סימולטור → ingest → analyze → recommend → DB).
- ✅ cold-start: GitHub Action `keepalive.yml` מ-ping כל 10 דק'. **טיפ דמו: פתח את האתר דקה לפני** (חימום ראשוני אם נרדם).

## נותר (איכות, לא חוסם דמו)
- 🟡 **bystander מסווג כ-victim** — `ml_service` מסווג תפקיד לפי `sender==child ? aggressor : victim`. זיהוי "צופה" דורש לדעת מיהו ה**יעד** (לא רק השולח). **משימת זוג ML:** להוסיף שדה `child_name`/יעד לחוזה A + לוגיקת bystander במודל. לא לתקן ב-hack חד-צדדי (משנה חוזה משותף).
- 🟡 **ניקוי נתונים:** ה-DB של Render צבר התראות בדיקה (כולל קבוצת "בדיקת WS חי"). לדאטה נקי לדמו: FS-A מפעיל restart ל-Render (אם SQLite ephemeral → מתאפס) ואז seed נקי אחד (escalation=victim + aggressor), או `POST /demo/seed` אידמפוטנטי.
- 🟡 **ללא `ANTHROPIC_API_KEY`** → המלצות = template (תקין). עם מפתח → LLM דינמי.

---

## 🤖 מודלים אמיתיים מקומית למצגת השופטים (היברידי + ngrok)

הענן (Render) נשאר על `USE_MODEL=false` (keyword fallback) — יציב, ללא OOM/cold-start על free tier.
המודלים האמיתיים (toxicity `OpenCensor-H1` / NSFW / deepfake) רצים רק על לפטופ חזק, לפיץ':

1. **סביבה:** Python **3.11/3.12** (לא 3.14 — אין wheels ל-torch).
   `python3.12 -m venv .venv && source .venv/bin/activate`
   `pip install -r backend_api/requirements.txt -r ml_service/requirements.txt`
2. **הרצה עם מודל אמיתי:** `USE_MODEL=true uvicorn backend_api.main:app --host 0.0.0.0 --port 8000`
   (הטעינה הראשונה מורידה מודלים מ-HuggingFace — לחמם **לפני** המצגת ע"י ingest אחד.)
3. **חשיפה החוצה:** `ngrok http 8000` → `https://<id>.ngrok.app`.
4. **בזמן המצגת בלבד:** ב-Vercel מעדכנים `VITE_API_BASE=https://<id>.ngrok.app` (redeploy), או
   מריצים את הפרונט מקומית מול ה-ngrok. השופטים רואים ציוני רעילות/deepfake אמיתיים בלייב.
5. **אחרי המצגת:** מחזירים `VITE_API_BASE` לכתובת Render → חזרה למצב היציב.

> אין צורך לפצל ML לשירות `MODEL_URL` נפרד: המודלים רצים בתוך תהליך ה-backend, ו-ngrok על כל
> ה-backend נותן בדיוק אותה תוצאה — ללא רכיבים חדשים ובלי לשבור את ה-fallback בענן.

## 🔧 ניקוי פריסה (מומלץ אחרי ההקאתון)
- **Render מושך את ענף `fs-server`, לא `main`.** קודם ב-fast-forward ל-`main` כך שהבקאנד החי
  מריץ את כל קוד ה-v2. לאיחוד: Render → Settings → **Branch → `main`**, ואז למחוק `fs-server`.
- ✅ **v2 חי אומת:** `/alerts` מחזיר 9 התראות (בריונות+דיסאינפורמציה, esc police+none); ingest חי של
  הודעת חשד → `alert_type=disinformation`; seed-on-empty הוא ברירת מחדל (DB לא נשאר ריק).
