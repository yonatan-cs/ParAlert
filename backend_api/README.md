# backend_api/ — הליבה וה-API (Dev 2)

המוח המקשר. מקבל הודעות, קורא ל-ML ול-LLM כקופסה שחורה, שומר התראות, מגיש לדשבורד.

## הרצה
```bash
cd backend_api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Swagger אינטראקטיבי: http://localhost:8000/docs

## Endpoints
| Method | Path | תיאור |
|--------|------|-------|
| `GET`  | `/health` | בדיקת חיים |
| `POST` | `/ingest` | הודעת וואטסאפ נכנסת (חוזה A) → מנתח → יוצר Alert אם רעיל |
| `GET`  | `/alerts?child_id=` | רשימת התראות לדשבורד (חוזה C) |

## תלויות (black box)
- `ml_service.analyzer.ToxicityAnalyzer` — Dev 1
- `simulator_and_logic.recommendation_engine.generate_recommendation` — Dev 4

שתיהן עטופות ב-try/except + import מוגן. אם מודול של חבר עוד לא מוזג — הבקאנד עולה עם stub.

## משימות
- [ ] להפוך ל-`use_model=True` כשמודל Dev 1 מוכן
- [ ] (אופ') WebSocket לדחיפת התראות בזמן אמת לדשבורד
- [ ] כוונון `ALERT_THRESHOLD`

## DB
SQLite ב-`safenet.db` (נוצר אוטומטית, ב-`.gitignore`). טבלה אחת: `alerts`.
