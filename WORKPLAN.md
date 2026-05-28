# 🗂️ WORKPLAN — חלוקת עבודה וצ'קליסט פתיחה

4 מפתחים, 2 זוגות. הסימולטור אחרון (אחרי שיש pipeline עובד).
התכנית המלאה: [`Idea+Plan.md`](./Idea+Plan.md) · החוזים: [`contracts/`](./contracts/)

---

## מפת בראנצ'ים

| בראנץ' | זוג | תיקייה |
|--------|-----|--------|
| `ml` | זוג ML (2) | `ml_service/` |
| `fullstack` | זוג Fullstack (2) | `backend_api/` + `frontend_dashboard/` |
| `main` | — | בסיס משותף. מיזוג רק כשעובד מקצה לקצה |

**כלל ברזל:** כל מפתח בעלים של קבצים נפרדים. אף אחד לא נוגע בקובץ של אחר. תקשורת רק דרך החוזים.

---

## שלב 0 — כולם יחד (15 דק', לפני קוד)

- [ ] לעבור על `contracts/schemas.py` — לאשר 3 חוזים (A: הודעה, B: ניתוח, C: התראה)
- [ ] לא משנים שדה בחוזה בלי הסכמת כולם
- [ ] כל אחד: `git fetch && git checkout <branch>`, להקים venv, `pip install -r requirements.txt`

---

## זוג ML — בראנץ' `ml`

פיצול קבצים: `analyzer.py` (ML-1) ↔ `role_classifier.py` (ML-2).
`analyzer.py` מייבא `classify_role`/`classify_category`. **החוזה הפנימי = חתימות הפונקציות.**

### ML-1 — `analyzer.py` (ניקוד רעילות + מודל)
- [ ] `python ml_service/analyzer.py` רץ ב-fallback (כבר עובד) — לוודא
- [ ] לטעון מודל HF (`unitary/multilingual-toxic-xlm-roberta` או `DictaBERT`)
- [ ] לכוון `_score` לפלט המודל האמיתי (0–1)
- [ ] לוודא `analyze()` עדיין לא זורק לעולם (try/except מסביב)
- [ ] (אופ') `vision.py` נפרד לזיהוי תמונות

### ML-2 — `role_classifier.py` (תפקיד + קטגוריה)
- [ ] להחליף heuristics ב-`classify_category` בסיווג אמיתי
- [ ] להחליף heuristics ב-`classify_role` (תוקף/קורבן)
- [ ] להוסיף לוגיקת `bystander` (הודעה רעילה בין שני אחרים, הילד רק נוכח)
- [ ] לבדוק מול תסריטי השיחה ב-`simulator_and_logic/conversations/`

---

## זוג Fullstack — בראנץ' `fullstack`

קבצים נפרדים: `backend_api/` (FS-1) ↔ `frontend_dashboard/` (FS-2). אפס התנגשות.

### FS-1 — `backend_api/` (שרת + DB) ← מתחיל ראשון, משחרר את כולם
- [ ] `uvicorn main:app --port 8000` — לוודא `/docs` עולה
- [ ] `GET /alerts` מחזיר (כרגע ריק/stub), `POST /ingest` מקבל חוזה A
- [ ] לחבר `ToxicityAnalyzer` מ-`ml` (כרגע stub — לעבור ל-`use_model=True` כשמוכן)
- [ ] לכוון `ALERT_THRESHOLD`
- [ ] (אופ') WebSocket לדחיפת התראות בזמן אמת

### FS-2 — `frontend_dashboard/` (דשבורד)
- [ ] לפתוח `demo.html` — עובד מיד מול mock (לוודא)
- [ ] להקים React+Vite+Tailwind (`npm create vite@latest app`)
- [ ] קומפוננטת `AlertCard` לפי חוזה C: קבוצה, תפקיד, מד רעילות, בועות, המלצה
- [ ] משיכה מ-`GET /alerts` + polling/ריענון
- [ ] אנימציה כשהתראה חדשה קופצת

---

## שלב אחרון — `simulator_and_logic/` (זוג Fullstack)

אחרי שהבקאנד יציב. שני קבצים מנותקים, כבר כתובים:
- [ ] `recommendation_engine.py` — להכניס `ANTHROPIC_API_KEY`, לכוון `SYSTEM_PROMPT`
- [ ] עוד תסריטים ב-`conversations/` (צופה, תוקף, שיחה רגילה ל-false-positive)
- [ ] `python simulator.py` מול השרת החי — לכוון קצב, להריץ את תרחיש הדמו

---

## סדר תלויות

```
FS-1 (שרת) ──► משחרר את ML / FS-2 / סימולטור
ML-1+ML-2 ──► analyzer מחזיר ניתוח אמיתי ──► FS-1 מחבר use_model=True
FS-2 ──► דשבורד מול /alerts
סימולטור (אחרון) ──► מזרים שיחה, מדגים הכל זורם
```

**מתחילים מ-FS-1.** הכל מוכן ב-fallback — הדמו לא קורס גם בלי מודל/LLM.
