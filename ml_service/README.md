# ml_service/ — מנוע הזיהוי (זוג ML — 2 מפתחים)

קופסה שחורה לבקאנד. מקבל `IncomingMessage` (חוזה A), מחזיר `AnalysisResult` (חוזה B). **לא נוגע ב-HTTP.**

## חלוקה בין שני מפתחי ML (קבצים נפרדים, אפס התנגשות)
| מפתח | קובץ | אחריות |
|------|------|--------|
| ML Dev 1 | `analyzer.py` | ניקוד רעילות (מודל HF) + אורקסטרציה |
| ML Dev 2 | `role_classifier.py` | סיווג תפקיד (תוקף/קורבן/צופה) + קטגוריה |

`analyzer.py` מייבא `classify_role` / `classify_category` מ-`role_classifier.py`.
**החוזה הפנימי** = החתימות של שתי הפונקציות. לא משנים בלי לתאם בין השניים.

## הרצה
```bash
cd ml_service
pip install -r requirements.txt
python analyzer.py          # smoke test (fallback mode, ללא מודל)
```

## API פנימי
```python
from ml_service.analyzer import ToxicityAnalyzer
analyzer = ToxicityAnalyzer(use_model=True)   # use_model=False = heuristic מהיר
result = analyzer.analyze(message)            # תמיד מחזיר AnalysisResult, לא זורק
```

## משימות
**ML Dev 1 (`analyzer.py`):**
- [ ] טעינת מודל HF (`unitary/multilingual-toxic-xlm-roberta` או `DictaBERT`)
- [ ] כוונון `_score` לפלט המודל האמיתי
- [ ] (אופ') זיהוי תמונות — OpenAI Vision / מודל NSFW של HF (קובץ נפרד `vision.py`)

**ML Dev 2 (`role_classifier.py`):**
- [ ] להחליף את ה-heuristics ב-`classify_category` / `classify_role` בסיווג אמיתי
- [ ] לוגיקת `bystander` (הודעה רעילה בין שני אחרים, הילד רק נוכח)

## הערות
- `analyze()` עטוף ב-try/except ותמיד מחזיר תוצאה תקינה — הדמו לא קורס.
- אם המודל לא נטען (OOM/אופליין) → נופל אוטומטית ל-keyword heuristic.
