# 🤖 הרצת המודלים האמיתיים מקומית (ML service + ngrok)

מדריך להרצת `ml_service/server.py` עם המודלים האמיתיים (OpenCensor toxicity / NSFW / deepfake)
על **מכונה חזקה**, וחיבורה ל-backend החי ב-Render דרך `ML_SERVICE_URL`.

**הארכיטקטורה:** Render נשאר light (keyword, בלי torch). כש-`USE_MODEL=true` + `ML_SERVICE_URL` מוגדרים,
ה-backend מנתב את הניתוח לשירות הזה (מודלים אמיתיים) דרך ngrok. כל כשל → fallback אוטומטי ל-keyword (לא קורס).

```
Judge → אתר (Vercel) → POST /analyze → Render → ngrok → ml_service/server.py (מודלים אמיתיים)
                                              └─ כשל/לא מוגדר → keyword דו-לשוני
```

---

## דרישות מקדימות
- **Python 3.11 או 3.12** (לא 3.13/3.14 — אין wheels ל-torch). בדיקה: `python3.12 --version`
  - Mac: `brew install python@3.12`
  - Windows: הורדה מ-python.org, או `winget install Python.Python.3.12`
  - Linux: `sudo apt install python3.12 python3.12-venv`
- **ngrok** — חשבון חינמי ב-[ngrok.com](https://ngrok.com) + authtoken.
- GPU אופציונלי (torch ישתמש ב-CUDA אוטומטית אם קיים) — CPU גם עובד.

## שלב 1 — קוד
```bash
git clone https://github.com/yonatan-cs/Hackathon-Project.git
cd Hackathon-Project
```

## שלב 2 — סביבה וירטואלית (3.12)
```bash
# Mac / Linux
python3.12 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

## שלב 3 — התקנת תלויות ה-ML
```bash
pip install -U pip
pip install -r ml_service/requirements.txt
```
⏳ torch כבד (~2-3GB), לוקח כמה דקות. (אם `av` נכשל בהתקנה — זה רק לווידאו, אפשר להמשיך.)

## שלב 4 — הרצת ה-ML service
```bash
# מ-root של הריפו, כש-venv פעיל
uvicorn ml_service.server:app --host 0.0.0.0 --port 8100
```
הרצה ראשונה מורידה את המודלים מ-HuggingFace (פעם אחת). חכו ל-`Application startup complete`.

בדיקה + **חימום** (אינפרנס ראשון איטי):
```bash
curl http://localhost:8100/health
# מצופה:  "text_model":"LikoKIko/OpenCensor-H1"   ← לא "keyword-fallback" = המודל האמיתי נטען ✅

curl -X POST http://localhost:8100/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"אתה אפס מטומטם"}'
```

## שלב 5 — חשיפה עם ngrok
```bash
ngrok config add-authtoken <ה-TOKEN-שלך>   # פעם אחת
ngrok http 8100
```
העתיקו את כתובת ה-`Forwarding`: `https://<id>.ngrok-free.app`. **השאירו את הטרמינל פתוח.**

## שלב 6 — להצביע את Render לשם
ב-Render dashboard → service `safenet-backend` → **Environment**:
- `USE_MODEL` = `true`
- `ML_SERVICE_URL` = `https://<id>.ngrok-free.app`  (בלי `/` בסוף)
- **Save** → redeploy אוטומטי (~30–60 שניות).

## שלב 7 — אימות חי
```bash
curl https://safenet-backend-cnmy.onrender.com/health
# מצופה:  "ml_routing": true , "ml_service":"https://<id>.ngrok-free.app"

curl -X POST https://safenet-backend-cnmy.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"אתה אפס מטומטם"}'
# model_used = "LikoKIko/OpenCensor-H1"  (לא keyword-fallback)
```
באתר, בצ'אט הקבוצתי — התג יתהפך ל**"מודל אמיתי"** והציונים יהיו של המודל.
קישור ישיר לשופט: `https://hackathon-project-tau-seven.vercel.app/?lang=en`

---

## במהלך המצגת (להשאיר רץ על המכונה החזקה)
- **טרמינל 1:** `uvicorn ml_service.server:app --host 0.0.0.0 --port 8100`
- **טרמינל 2:** `ngrok http 8100`
- (Render env מוגדר פעם אחת)
- ⚠️ אם המחשב נרדם / ngrok מתאתחל → הכתובת משתנה → עדכנו שוב את `ML_SERVICE_URL` ב-Render.

## אחרי המצגת (חזרה ליציב)
Render → Environment → מחקו `ML_SERVICE_URL` (או `USE_MODEL=false`) → Save → חזרה ל-keyword היציב.

## תקלות נפוצות
| תופעה | סיבה / פתרון |
|-------|---------------|
| `/health` מראה `keyword-fallback` | torch לא נטען → ודאו Python 3.11/3.12, `pip show torch`, התקינו מחדש |
| Render `ml_routing: false` | `USE_MODEL` לא `true`, או `ML_SERVICE_URL` ריק |
| timeout בקריאה ראשונה | חממו קודם (שלב 4); אפשר להעלות `ML_TIMEOUT` (env ב-Render, ברירת מחדל 30) |
| ngrok נפל באמצע | ה-backend חוזר אוטומטית ל-keyword — לא קורס. הרימו ngrok מחדש ועדכנו `ML_SERVICE_URL` |
| מודלי מדיה (NSFW/deepfake) לא נטענים | רצים lazy בקריאת המדיה הראשונה; ודאו `pillow`/`opencv-python`/`transformers` הותקנו |

> שירות זה מחזיר את חוזה `contracts.schemas.AnalyzeResponse`; ה-backend מוסיף עליו credibility/alert.
> ראו גם `DEPLOY.md` לתקציר.
