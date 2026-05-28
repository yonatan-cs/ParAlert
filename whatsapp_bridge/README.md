# whatsapp_bridge/ — אינטגרציה אמיתית לוואטסאפ (ה-must-have של השופט)

מקשר את האפליקציה כ-"מכשיר מקושר" בוואטסאפ. ההורה סורק QR (בדיוק כמו WhatsApp Web),
והודעות קבוצה אמיתיות זורמות לבקאנד כ-**חוזה A** → `POST /ingest`.

**Drop-in לסימולטור:** אותו חוזה בדיוק → אפס שינוי בבקאנד. הסימולטור נשאר fallback לבמה.

## הרצה
מדלגים על ה-Chromium המובנה של Puppeteer (הורדה כבדה ולא יציבה) — הגשר מזהה אוטומטית
Chrome/Edge מותקן במערכת.
```bash
cd whatsapp_bridge
# bash / macOS / Linux:
PUPPETEER_SKIP_DOWNLOAD=true npm install
# Windows PowerShell:
#   $env:PUPPETEER_SKIP_DOWNLOAD="true"; npm install
node index.js               # מפעיל Chrome + מדפיס QR בטרמינל
# בטלפון: WhatsApp > הגדרות > מכשירים מקושרים > קישור מכשיר > סרוק
```
אחרי סריקה: הסשן נשמר ב-`.wwebjs_auth/` — לא צריך לסרוק שוב בהרצה הבאה.

## איך זה ממופה לחוזה A
| שדה | מקור |
|------|------|
| `message_id` | `msg.id._serialized` |
| `group_name` | `chat.name` |
| `sender_id` / `sender_name` | `msg.author` + contact pushname |
| `child_id` | חשבון הוואטסאפ המקושר (`client.info.wid`) |
| `text` | `msg.body` |
| `context_before` | חלון מתגלגל של 2 הודעות אחרונות בצ'אט |

משתמש ב-`message_create` (לא רק `message`) כדי לתפוס גם הודעות **יוצאות** של הילד → זיהוי הילד כתוקף.

## הגדרות (env, אופציונלי)
- `BACKEND_URL` (ברירת מחדל `http://localhost:8000/ingest`)
- `GROUPS_ONLY` (`true` = רק קבוצות)
- `CHROME_PATH` — נתיב מפורש ל-`chrome.exe`/`msedge.exe` אם הזיהוי האוטומטי נכשל

## משימות
- [ ] `npm install` + סריקת QR ראשונה על מספר burner/דמו
- [ ] לוודא הודעות קבוצה מגיעות ל-`/ingest` (לבדוק לוג `🚨 ALERT`)
- [ ] (אופ') הורדת מדיה (`msg.downloadMedia()`) → ניתוח תמונות
- [ ] (אופ') `context_after` ע"י עיכוב שליחה בהודעה אחת

## אזהרות
- **לא רשמי** (הפרת ToS של וואטסאפ). ban אפשרי תוך שבועות → **השתמשו במספר burner/דמו בלבד**, לא אישי.
- לדמו חד-פעמי זה מצוין. לפרודקשן אמיתי צריך WhatsApp Business API דרך BSP.
