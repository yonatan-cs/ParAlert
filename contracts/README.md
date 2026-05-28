# contracts/ — מקור האמת היחיד

כל המודולים מדברים אך ורק דרך הקבצים כאן. **אסור לשנות שדה בלי ליידע את כל הצוות.**

| קובץ | תיאור |
|------|-------|
| `schemas.py` | מודלי Pydantic לכל החוזים (A/B/C) + `severity_from_score()` |
| `mock_alerts.json` | התראות לדוגמה — Frontend מתחיל מולן עד שהבקאנד מוכן |

## החוזים
- **A — `IncomingMessage`**: Simulator → Backend (`POST /ingest`)
- **B — `AnalysisResult`**: ML Service → Backend
- **C — `Alert`**: Backend → Frontend (`GET /alerts`)

## ייבוא מהמודולים
כל מודול מוסיף את שורש הפרויקט ל-path, או מתקין כחבילה. הדרך הפשוטה בהקאתון:
```python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from contracts.schemas import IncomingMessage, AnalysisResult, Alert
```
