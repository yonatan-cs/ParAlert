# ml_service/ — מנוע הזיהוי (Dev 1)

קופסה שחורה לבקאנד. מקבל `IncomingMessage` (חוזה A), מחזיר `AnalysisResult` (חוזה B). **לא נוגע ב-HTTP.**

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
- [ ] טעינת מודל HF (`unitary/multilingual-toxic-xlm-roberta` או `DictaBERT`)
- [ ] להחליף את ה-heuristics ב-`_classify_category` / `_classify_role` בסיווג אמיתי
- [ ] לוגיקת `bystander` (הודעה רעילה בין שני אחרים, הילד רק נוכח)
- [ ] (אופ') זיהוי תמונות — OpenAI Vision / מודל NSFW של HF

## הערות
- `analyze()` עטוף ב-try/except ותמיד מחזיר תוצאה תקינה — הדמו לא קורס.
- אם המודל לא נטען (OOM/אופליין) → נופל אוטומטית ל-keyword heuristic.
