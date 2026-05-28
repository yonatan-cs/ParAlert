# 🗂️ WORKPLAN — חלוקת עבודה וצ'קליסט פתיחה

4 מפתחים, 2 זוגות. הסימולטור אחרון (אחרי שיש pipeline עובד).
התכנית המלאה: [`Idea+Plan.md`](./Idea+Plan.md) · החוזים: [`contracts/`](./contracts/)

---

## מפת בראנצ'ים

| בראנץ' | זוג | תיקייה |
|--------|-----|--------|
| `ml` | זוג ML (2) | `ml_service/` |
| `fullstack` | זוג Fullstack (2) | `backend_api/` + `frontend_dashboard/` + `whatsapp_bridge/` |
| `main` | — | בסיס משותף. מיזוג רק כשעובד מקצה לקצה |

> **דרישת השופט:** משהו שעובד אמיתי על פלטפורמה אחת → `whatsapp_bridge/` (וואטסאפ דרך QR). זה עכשיו deliverable בעדיפות גבוהה, לא אופציונלי.

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

## זוג Fullstack — 2 מפתחים, בראנץ' אישי לכל אחד

הזוג מתפצל ל-Inbound (שרת+וואטסאפ) ו-Outbound (דשבורד+דמו). כל אחד בראנץ' משלו.
מיזוג ל-`fullstack` (אינטגרציה) → אז `fullstack` → `main`.

| תפקיד | בראנץ' | קבצים |
|-------|--------|-------|
| **FS-A** (Inbound) | `fs-server` | `backend_api/` + `whatsapp_bridge/` |
| **FS-B** (Outbound) | `fs-dashboard` | `frontend_dashboard/` + `simulator_and_logic/` |
| אינטגרציה | `fullstack` | יעד מיזוג של שני הבראנצ'ים |

**כלל:** כל אחד נוגע רק בקבצים שלו. צריך שינוי בקובץ של השני? מבקשים, לא עורכים.

### 👤 FS-A — `fs-server` (שרת + וואטסאפ) ← מתחיל ראשון, משחרר את FS-B
**`backend_api/`:**
- [ ] `uvicorn main:app --port 8000` — `/docs`, `/health`, `/alerts`, `/ingest` (חוזה A)
- [ ] לחבר `ToxicityAnalyzer` מ-`ml` (stub → `use_model=True` כשמוכן), לכוון `ALERT_THRESHOLD`
- [ ] (אופ') WebSocket לדחיפת התראות

**`whatsapp_bridge/` ⭐ דרישת השופט:**
- [ ] `npm install` + `node index.js` → סריקת QR ממספר **burner** (לא אישי!)
- [ ] הודעות קבוצה אמיתיות מגיעות ל-`/ingest` (לוג `🚨 ALERT`)
- [ ] לבדוק מיפוי חוזה A (group_name, sender, child_id, context_before)

### 👤 FS-B — `fs-dashboard` (דשבורד + לוגיקת דמו)
**`frontend_dashboard/`:**
- [ ] `demo.html` מול mock (לוודא), אז React+Vite+Tailwind
- [ ] `AlertCard` לפי חוזה C: קבוצה, תפקיד, מד רעילות, בועות, המלצה
- [ ] משיכה מ-`GET /alerts` + polling, אנימציה להתראה חדשה

**`simulator_and_logic/` (fallback לבמה + המלצות):**
- [ ] `recommendation_engine.py` — `ANTHROPIC_API_KEY`, לכוון `SYSTEM_PROMPT`
- [ ] עוד תסריטים ב-`conversations/` (צופה, תוקף, שיחה רגילה ל-false-positive)
- [ ] `python simulator.py` מול השרת — לכוון קצב, תרחיש הדמו

### הממשק בין FS-A ל-FS-B (הצימוד היחיד)
- frontend (B) ← `GET /alerts` (חוזה C) של A
- simulator (B) → `POST /ingest` (חוזה A) של A
- `generate_recommendation()` (B) ← מיובא ע"י הבקאנד (A) כ-black box. **החתימה = החוזה.**

---

## סדר תלויות

```
FS-A: שרת ──► משחרר את כולם
        ├─► whatsapp_bridge ⭐ (הודעות אמיתיות → /ingest)   ← דרישת השופט
        └─► (FS-B מתחבר)
FS-B: דשבורד מול mock ──► אז מול /alerts ; simulator → /ingest (fallback)
ML-1+ML-2 ──► analyzer אמיתי ──► FS-A מחבר use_model=True
```

**מתחילים מ-FS-A (שרת).** הכל מוכן ב-fallback — הדמו לא קורס גם בלי מודל/LLM/וואטסאפ.
**עדיפות לשופט:** שרת → גשר וואטסאפ עובד מקצה לקצה. זה ה"עובד באמת".

---

## תוספות שופטים (פיצ'רים חדשים) — ראה [Idea+Plan §9](./Idea+Plan.md)

חוזה הורחב ב-`contracts/schemas.py` (הכל אופציונלי, backward-compatible): `escalation`,
`alert_type`, `credibility`, קטגוריות חדשות, `ChatBubble.media_*`, `escalation_from()`.

### ✅ FS-B (בוצע)
- AlertCard: באנר "פנייה למשטרה" (escalation), מדיה בבועות (חסום לרגיש 🔞), סקשן דיסאינפורמציה (מד אמינות + טענה + verdict + מקור).
- SummaryBar: ספירת "דורשות משטרה" + "דיסאינפורמציה". FilterBar: סינון "נחשף".
- `recommendation_engine`: טקסט הסלמה למשטרה/אובדנות. `fact_check.py`: credibility (Google Fact Check + fallback).
- `mock_alerts.json` עשיר (8 התראות, 7 קבוצות, מדיה).

### 👤 FS-A (backend)
- [ ] ב-`_build_alert`: `escalation = escalation_from(category, severity)` (ייבא מ-schemas) → התראות חיות מקבלות הסלמה.
- [ ] נתיב דיסאינפורמציה: כשהניתוח מחזיר `alert_type="disinformation"` — לצרף `credibility` (לקרוא ל-`fact_check.check_claim`).
- [ ] (אופ') מ-bridge: להעביר `media_type` ל-ingest כשיש מדיה.

### 👤 זוג ML
- [ ] סיווג קטגוריות חמורות (`sexual_harassment`, `nudity`, `self_harm`) + הסלמה מהמודל.
- [ ] זיהוי **תמונה/וידאו AI-generated** (deepfake) → מזין `credibility`.
- [ ] לוגיקת `exposed`/דיסאינפורמציה במנתח.
