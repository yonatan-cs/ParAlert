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

## 🤖 מודלים אמיתיים + צ'אט "נסו בעצמכם" למצגת (ML service + Cloudflare Tunnel)

הענן (Render) נשאר light: keyword fallback **ללא torch** (יציב, אפס OOM/cold-start). את ה-ML הכבד
מריצים על מכונה חזקה מקומית כשירות נפרד (`ml_service/server.py`), וה-backend ב-Render מנתב אליו דרך
`ML_SERVICE_URL`. כך השופטים מקבלים ציונים אמיתיים (OpenCensor toxicity / NSFW / deepfake) דרך טאב
**"נסו בעצמכם"** באתר — בלי לטעון torch ב-Render.

**הרצה (מכונה מקומית, Python 3.11/3.12 — לא 3.14, אין wheels ל-torch):**
1. `python3.12 -m venv .venv && source .venv/bin/activate`
2. `pip install -r ml_service/requirements.txt`
3. `uvicorn ml_service.server:app --host 0.0.0.0 --port 8100`  (טעינה ראשונה מורידה מודלים — לחמם!)
4. `cloudflared tunnel --url http://localhost:8100` → מעתיקים את כתובת ה-`https://<...>.trycloudflare.com`.
   (התקנה: `brew install cloudflared` / `winget install Cloudflare.cloudflared`. **ngrok נחסם ברשת האוני'** → Cloudflare על 443 לא נחסם.)
5. ב-Render → Environment: `USE_MODEL=true` + `ML_SERVICE_URL=https://<...>.trycloudflare.com` → Save (redeploy ~30ש').
6. אימות: `GET https://<backend>/health` מציג `"ml_routing": true`. חימום: שולחים הודעה אחת בטאב "נסו בעצמכם".

**זרימה:** שופט → טאב "נסו בעצמכם" (טקסט / קישור מדיה / העלאת קובץ) → `POST /analyze` או `/analyze/upload`
ל-Render → ניתוב ל-ML service (מודלים אמיתיים) → דוח חי בכרטיס; ואם רעיל/דיסאינפורמציה — גם **קופץ בדשבורד** (WS).

**חסין כשל:** אם ה-ML service/המנהרה נופלים → ה-backend חוזר אוטומטית ל-keyword הדו-לשוני (עברית+אנגלית)
ולא קורס. אחרי המצגת: מוחקים `ML_SERVICE_URL` ב-Render → חזרה למצב keyword היציב.
קישור ישיר לשופט: `…/?lang=en&tab=chat`.

> חלופה פשוטה יותר (בלי שירות נפרד): להריץ את כל ה-backend מקומית עם `USE_MODEL=true` + cloudflared ולהצביע
> `VITE_API_BASE` לשם. ה-ML service עדיף כי Render נשאר ציבורי ויציב וה-keyword fallback תמיד זמין.

## 🔧 ניקוי פריסה (מומלץ אחרי ההקאתון)
- **Render מושך את ענף `fs-server`, לא `main`.** קודם ב-fast-forward ל-`main` כך שהבקאנד החי
  מריץ את כל קוד ה-v2. לאיחוד: Render → Settings → **Branch → `main`**, ואז למחוק `fs-server`.
- ✅ **v2 חי אומת:** `/alerts` מחזיר 9 התראות (בריונות+דיסאינפורמציה, esc police+none); ingest חי של
  הודעת חשד → `alert_type=disinformation`; seed-on-empty הוא ברירת מחדל (DB לא נשאר ריק).
