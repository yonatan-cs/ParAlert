# 🛡️ ParAlert — מערכת התראות למניעת בריונות ברשת

> מסמך אב לפרויקט ההקאתון. כל חבר צוות קורא את **השלב הקריטי** ואת **החוזים (Contracts)** לפני שכותב שורת קוד.

---

## 1. הרעיון בקצרה

מערכת שסורקת שיחות וואטסאפ של ילדים ומתריעה להורה כשמזוהה בריונות.
ההתראה כוללת: ההודעה הבעייתית + קונטקסט (הודעה לפני/אחרי), ציון רעילות, פרטים מזהים (מי→מי), והמלצה לפעולה.

**3 זוויות התקפה:**
1. הילד שלי **אלים** כלפי אחרים (תוקף / aggressor)
2. אחרים אלימים **כלפי הילד שלי** (קורבן / victim)
3. הילד שלי **חשוף** לאלימות (צופה מהצד / bystander)

**קהל יעד:** הורים. מספיק אותם הורים שכן יתקינו — כי הורה שמתקין הוא הורה שיפעל.

**סקופ הדמו:** מתחברים לפלטפורמה אחת אמיתית — **וואטסאפ**, דרך `whatsapp-web.js` (ההורה סורק QR כמו WhatsApp Web). הודעות קבוצה אמיתיות זורמות למערכת. במקביל יש **סימולטור** שמזרים שיחות מדומות כ-fallback לבמה. שניהם פולטים את אותו חוזה A — אז הבקאנד אדיש למקור.

> דרישת השופט: "משהו שעובד באמת על פלטפורמה אחת לפחות" → `whatsapp_bridge/` הוא ה-deliverable הזה.

---

## 2. השלב הקריטי — שעה ראשונה (אל תכתבו קוד!)

שבו יחד, נעלו את שני ה-JSON-ים בתיקיית [`contracts/`](./contracts/). כל המודולים מדברים אך ורק דרכם.
ברגע שהחוזים נעולים — כל אחד מתפצל לבראנץ' שלו ועובד עצמאית מול Mock.

### חוזה A — הודעה נכנסת (Simulator → Backend)
```json
{
  "message_id": "msg_12345",
  "group_name": "כיתה ו'2 - בלי המורה",
  "sender_id": "yonatan_1",
  "sender_name": "יונתן",
  "child_id": "child_001",
  "text": "איזה אפס אתה, אל תבוא מחר",
  "media_url": null,
  "timestamp": "2026-05-28T14:20:00",
  "context_before": ["מתי קובעים למשחק?"],
  "context_after": []
}
```

### חוזה B — תוצאת ניתוח (ML Service → Backend)
```json
{
  "message_id": "msg_12345",
  "is_toxic": true,
  "toxicity_score": 0.91,
  "category": "harassment",
  "role_of_child": "victim",
  "aggressor": "dani_2",
  "victim": "yonatan_1",
  "explanation": "השפלה ישירה + איום על השתתפות חברתית",
  "model_used": "dictabert-toxicity"
}
```
`role_of_child` ∈ `aggressor` | `victim` | `bystander` | `none`
`category` ∈ `harassment` | `threat` | `exclusion` | `hate_speech` | `sexual` | `none`

### חוזה C — אובייקט התראה (Backend → Frontend)
```json
{
  "alert_id": "alert_001",
  "child_id": "child_001",
  "severity": "high",
  "toxicity_score": 0.91,
  "role_of_child": "victim",
  "category": "harassment",
  "group_name": "כיתה ו'2 - בלי המורה",
  "trigger_message": {
    "sender_name": "דני",
    "text": "איזה אפס אתה, אל תבוא מחר",
    "timestamp": "2026-05-28T14:20:00"
  },
  "context_before": [{"sender_name": "יונתן", "text": "מתי קובעים למשחק?"}],
  "context_after": [],
  "recommendation": "הילד שלך היה קורבן להשפלה. מומלץ לשוחח איתו בנחת ולשקול פנייה למחנכת.",
  "created_at": "2026-05-28T14:20:03"
}
```
`severity` ∈ `low` | `medium` | `high` (נגזר מ-`toxicity_score`: <0.5 low, 0.5–0.8 medium, >0.8 high)

---

## 3. Tech Stack

| שכבה | טכנולוגיה | למה |
|------|-----------|-----|
| Backend & API | **FastAPI (Python)** | מהיר, Swagger מובנה לתיעוד החוזים, משתלב עם ML |
| Frontend | **React + Vite + Tailwind + shadcn/ui** | מראה מקצועי במינימום זמן |
| Database | **SQLite** (קובץ מקומי) | אפס הגדרה. שדרוג אופציונלי ל-Supabase ל-realtime |
| ML | **HuggingFace `transformers`** | מודלי toxicity מוכנים + fine-tuning קל |
| LLM (המלצות) | **API (Anthropic / OpenAI)** | יצירת טקסט המלצה אמפתי ופדגוגי |
| **WhatsApp** | **Node.js + `whatsapp-web.js`** | אינטגרציה אמיתית. QR linked-device, קורא הודעות קבוצה |
| Realtime (אופ') | WebSocket / polling | הקפצת התראה בזמן אמת בדשבורד |

### למה whatsapp-web.js (סיכום המחקר)
- **על-נרטיב:** המוצר הוא וואטסאפ. לא Telegram/Discord שמחוץ לקהל.
- **פשוט באמת:** Node + סריקת QR, `message` event מחזיר הודעות קבוצה.
- **drop-in:** פולט חוזה A → אפס שינוי בבקאנד (כמו הסימולטור).
- נדחו: Facebook/Messenger (Graph API דורש app review — לא ריאלי בהקאתון), Telegram/Discord (קהל לא נכון).
- **אזהרה:** לא רשמי (הפרת ToS), ban אפשרי תוך שבועות → **מספר burner/דמו בלבד**. לדמו חד-פעמי מצוין.

---

## 4. חלוקת עבודה

> **החלוקה הפעילה היא 2 זוגות** — ראה [`WORKPLAN.md`](./WORKPLAN.md) לצ'קליסט פתיחה ובעלות קבצים מדויקת.
> זוג ML (`ml_service/`) + זוג Fullstack (`backend_api/` + `frontend_dashboard/` + `whatsapp_bridge/`).
> הסעיף למטה הוא הפירוט המקורי לפי תפקידים — עדיין תקף כתיאור אחריות.

**עיקרון ברזל:** כל אחד בעלים של קבצים נפרדים. אף אחד לא נוגע בקובץ של אחר. תקשורת רק דרך החוזים.

**שני מקורות דאטה, אותו חוזה A:** `whatsapp_bridge/` (אמיתי, Node) ו-`simulator_and_logic/simulator.py` (מדומה, fallback). הבקאנד אדיש למי ששלח.

### 👤 מפתח 1 — ML / AI Engineer → [`ml_service/`](./ml_service/)
**אחריות:** מנוע הזיהוי. מקבל הודעה+קונטקסט (חוזה A), פולט ניתוח (חוזה B).
- טעינת מודל toxicity מ-HuggingFace
- מחלקת `ToxicityAnalyzer` עם `analyze(message) -> AnalysisResult`
- סיווג תפקיד הילד: תוקף/קורבן/צופה
- (אופ') זיהוי תמונות — OpenAI Vision או מודל NSFW של HF
- **בלי חיכוך:** כותב מחלקות Python נטו. לא נוגע ב-HTTP. מפתח 2 מייבא אותו.

### 👤 מפתח 2 — Backend / Core → [`backend_api/`](./backend_api/)
**אחריות:** המוח המקשר. ניהול זרימת הנתונים + DB.
- שרת FastAPI
- Endpoints: `POST /ingest` (הודעה חדשה), `GET /alerts` (לדשבורד)
- חיבור SQLite (היסטוריה + התראות)
- ייבוא `ToxicityAnalyzer` כקופסה שחורה → אם score גבוה → יצירת Alert
- קריאה ל-`recommendation_engine` של מפתח 4
- **בלי חיכוך:** משתמש במודל של מפתח 1 ובמנוע של מפתח 4 כ-black box.

### 👤 מפתח 3 — Frontend → [`frontend_dashboard/`](./frontend_dashboard/)
**אחריות:** דשבורד ההורה. החזית של המוצר — מה שהשופטים יראו.
- ממשק נקי שמתריע בזמן אמת
- תצוגת התראה: הודעה פוגענית מודגשת + בועות צ'אט לפני/אחרי
- מד רעילות ויזואלי (גרף/חיווי)
- "המלצה לפעולה" בולטת
- **בלי חיכוך:** עובד מול `GET /alerts` או מול `mock_data.json` עד שהבקאנד מוכן.

### 👤 מפתח 4 — Data Sim / LLM → [`simulator_and_logic/`](./simulator_and_logic/)
**אחריות:** הדמו קם ונופל על אמינות הדאטה + ההמלצות הדינמיות.
- **וואטסאפ מזויף:** סקריפט ששולח בקשות HTTP ל-`/ingest` בקצב משתנה, עם שיחות מדומות (רגילות + הצקות מדורגות)
- **מנוע המלצות:** `generate_recommendation(analysis, context) -> str` — שולח ל-LLM פרומפט מוקפד ומחזיר המלצה פדגוגית להורה
- **בלי חיכוך:** מזין דאטה מבחוץ כ-Client + מספק סקריפט מנותק שמפתח 2 מייבא.

---

## 5. המודלים (HuggingFace)

אימון מאפס בעברית במהלך הקאתון = אסון. אין מספיק זמן/דאטה. הגישה: מודל מוכן + fine-tuning קליל.

1. **בסיס Multilingual:** `unitary/multilingual-toxic-xlm-roberta` — toxicity רב-לשוני, סביר בעברית.
2. **עברית ייעודי:** `DictaBERT` / `heBERT`. אם נמצא dataset קטן בעברית — fine-tuning ל-Sequence Classification. ירשים שופטים.
3. **Fall-Back (חובה!):** סקריפט שקורא ל-API של Anthropic/OpenAI עם System Prompt חזק: "האם הטקסט מכיל בריונות ומאיזה סוג (תוקף/קורבן/צופה)?". המטרה — מוצר עובד תמיד.

---

## 6. טיפים לדמו

- **זווית ההורה:** התחילו מסימולטור שמראה שיחת קבוצה "רגילה" שמתדרדרת לחרם. אז עברו למסך ההורה — ההתראה קופצת בזמן אמת.
- **Killer feature — המלצה לפעולה:** כולם יודעים לצעוק "יש בעיה". הורה שרואה שהילד שלו *הבריון* לא יודע מה לעשות. ההמלצה האמפתית, מבוססת הפסיכולוגיה, היא מה שמנצח.
- **Error handling קיצוני:** עטפו כל קריאת ML/API ב-`try-except` שמחזיר Mock במקרה קריסה. הדמו לא נתקע על הבמה לעולם.

---

## 7. כללי עבודה (Git)

- כל אחד עובד על **בראנץ' משלו**: `dev1-ml`, `dev2-backend`, `dev3-frontend`, `dev4-sim`.
- מיזוג ל-`main` רק כשהחוזה עובד מקצה לקצה.
- לא נוגעים בתיקייה של אחר. נקודה.

---

## 8. סדר עבודה מומלץ (Timeline)

1. **שעה 1:** כולם יחד — נעילת החוזים ב-`contracts/`. אישור מבנה ה-JSON.
2. **שעות 2–4:** עבודה מקבילה מול Mock. כל אחד בתיקייה שלו.
   - מפתח 1: analyzer מחזיר תוצאה (אפ' עם מודל פשוט/mock קודם)
   - מפתח 2: שרת עולה, endpoints מחזירים נתונים קשיחים
   - מפתח 3: דשבורד מציג `mock_data.json`
   - מפתח 4: סימולטור שולח ל-endpoint, מנוע המלצות מחזיר טקסט
3. **שעות 5–6:** אינטגרציה. מחברים backend↔ml↔llm. frontend↔backend.
4. **שעות 6+:** ליטוש דמו, fall-backs, חזרות על התרחיש לבמה.

---

## 9. תוספות שופטים (raised after demo feedback)

### 9.1 הסלמה למשטרה — מקרים חמורים
מקרים חמורים מאוד (הטרדה מינית/סחיטה, הפצת תוכן עירום של קטין, איום פיזי מפורש, אובדנות)
מקבלים **המלצה חמה לפנייה למשטרה** (100) ו-105, ובאובדנות גם ער"ן 1201.
- חוזה: `Alert.escalation` ∈ `none|school|police` + `Category` הורחב (`sexual_harassment`, `nudity`, `self_harm`).
- כלל משותף: `escalation_from(category, severity)` ב-`contracts/schemas.py`.
- Backend (FS-A): לקבוע `escalation` ב-`_build_alert`. Frontend (FS-B): באנר אדום בולט "פנייה למשטרה — 100".
- Reco (FS-B): טקסט הסלמה מפורש בהמלצה.

### 9.2 מדד אמינות / דיסאינפורמציה (AI-generated)
הילד נחשף לתוכן כוזב/מזויף — תמונה/וידאו (deepfake) או טענה שגויה. "הילד שלך מאמין ש-X / נחשף לטענה לא נכונה".
- חוזה: `Alert.alert_type` ∈ `bullying|disinformation`, `Alert.credibility` = `{score, verdict, claim, source}`, role `exposed`.
- מקור: `simulator_and_logic/fact_check.py` — Google Fact Check Tools API (`GOOGLE_FACTCHECK_API_KEY`) + fallback היוריסטי. זיהוי תמונה/וידאו AI-generated = משימת ML.
- Frontend (FS-B): מד "אמינות" + הטענה + verdict + מקור, תג "דיסאינפורמציה".

### 9.3 דמו עשיר
מספר קבוצות, יותר התראות, **תמונות/וידאו** בבועות (`ChatBubble.media_url/media_type`; תוכן רגיש מוצג חסום 🔞).
`contracts/mock_alerts.json` = 8 התראות, 7 קבוצות, כל הזוויות + משטרה + דיסאינפורמציה + מדיה.
