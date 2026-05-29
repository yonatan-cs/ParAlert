# ParAlert

מערכת התראות בזמן-אמת על פגיעה בילדים ברשת.

ParAlert is a real-time child-safety alerting platform for parents. It monitors chat messages and media, detects harmful dynamics around children, and gives parents the context and guidance they need before reacting out of panic.

## Live Demo

- Parent dashboard: [https://hackathon-project-tau-seven.vercel.app](https://hackathon-project-tau-seven.vercel.app)
- Try-it chat view: [https://hackathon-project-tau-seven.vercel.app/?lang=en&tab=chat](https://hackathon-project-tau-seven.vercel.app/?lang=en&tab=chat)
- Backend API: [https://safenet-backend-cnmy.onrender.com](https://safenet-backend-cnmy.onrender.com)

## The Problem

הורים כיום כמעט עיוורים למה שמתרחש בקבוצות הוואטסאפ של הילדים שלהם. חרמות, איומים, הפצת תמונות אינטימיות, דיסאינפורמציה ו-Deepfakes יכולים להתרחש מתחת לרדאר.

כאשר הורה מגלה על אירוע רק בדיעבד, לרוב חסר לו הקונטקסט המלא: מי התחיל, מה נאמר לפני, האם הילד שלו היה קורבן, תוקף או צופה מהצד, ומה הדרך הנכונה לדבר עם הילד בלי לשבור אמון.

## Our Solution

ParAlert analyzes text, images, and videos in real time and sends meaningful alerts to a clean parent dashboard. Each alert includes:

- The risky message or media.
- Severity level and category.
- The child's role in the situation: victim, aggressor, bystander, exposed, or none.
- Context before and after the message.
- A practical, empathetic recommendation for how the parent should respond.
- Escalation guidance for severe cases such as sexual extortion, nudity distribution, real threats, or self-harm.

## Core Capabilities

### Multi-Angle Detection

The system does more than classify content as good or bad. It tries to understand the social dynamic:

- Is the child being attacked?
- Is the child attacking someone else?
- Is the child watching a harmful event unfold?
- Is the child exposed to unsafe or manipulated media?

### Empathetic Parent Guidance

The recommendation engine turns a raw alert into a useful next step. Instead of leaving the parent with only a red warning, ParAlert explains how to approach the child calmly, what to ask, and when to involve school or authorities.

### Police Escalation

For extreme cases, the backend can mark an alert for police-level escalation. This is used for categories such as sexual exploitation, nudity distribution, credible threats, and self-harm risk.

### Media Safety and Deepfake Signals

ParAlert supports image and video URLs. The ML service downloads direct media files and analyzes them with HuggingFace vision models:

- NSFW / unsafe visual content detection.
- AI-generated image signal.
- Experimental video deepfake signal.

Important: the AI/deepfake score is currently treated as an additional signal, not the only reason to mark content as harmful. The safety score is the main trigger for harmful visual content.

### Try It Yourself

The dashboard includes an interactive bilingual chat experience for testing the models with text and media. This is useful for demos, judges, and developers who want to understand how the system reacts to different scenarios.

## Architecture

```mermaid
flowchart LR
    A["WhatsApp bridge / simulator"] --> B["FastAPI backend on Render"]
    C["Parent dashboard on Vercel"] <--> B
    B <--> D["SQLite alert store"]
    B <--> E["WebSocket alert stream"]
    B --> F["Optional remote ML service"]
    F --> G["HuggingFace text model"]
    F --> H["HuggingFace vision models"]
    B --> I["Recommendation engine"]
```

ParAlert uses a hybrid architecture:

- The frontend runs on Vercel.
- The API runs on Render with FastAPI.
- Alerts stream live through WebSockets.
- Demo data can come from the simulator or the WhatsApp bridge.
- Heavy ML inference can run on a stronger local machine and be exposed through a secure tunnel.
- If the remote ML service is unavailable, the backend keeps the demo alive with lightweight fallback logic.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, Vercel |
| Backend | FastAPI, SQLite, WebSockets, Render |
| Text ML | HuggingFace `LikoKIko/OpenCensor-H1` plus Hebrew context heuristics |
| Media Safety | HuggingFace `Falconsai/nsfw_image_detection` |
| Image AI Signal | HuggingFace `capcheck/ai-image-detection` |
| Video Deepfake Signal | HuggingFace VideoMAE-based detector |
| Recommendation Engine | LLM-backed guidance with template fallback |
| WhatsApp Demo Bridge | `whatsapp-web.js` proof-of-concept bridge |

## Main API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health check |
| `POST /ingest` | Ingest one chat message using the shared contract |
| `GET /alerts` | Fetch current alerts for the dashboard |
| `POST /analyze` | Analyze text and optional media URL directly |
| `POST /analyze/upload` | Analyze uploaded media |
| `POST /demo/seed` | Seed demo alerts |
| `WS /ws/alerts` | Live alert stream for the dashboard |

## Local Development

### Backend

```bash
cd backend_api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend_dashboard/app
npm install
npm run dev
```

Set the frontend API URL in `frontend_dashboard/app/.env`:

```bash
VITE_API_BASE=http://localhost:8000
```

For production, the Vercel environment should point to:

```bash
VITE_API_BASE=https://safenet-backend-cnmy.onrender.com
```

### Simulator

```bash
cd simulator_and_logic
pip install -r requirements.txt
python simulator.py
```

### Optional ML Service

Run the heavier HuggingFace models as a separate service:

```bash
pip install -r ml_service/requirements.txt
uvicorn ml_service.server:app --host 0.0.0.0 --port 8100
```

Then expose it to the backend with a tunnel and configure Render:

```bash
USE_MODEL=true
ML_SERVICE_URL=https://your-tunnel-url
```

## Environment Variables

| Variable | Service | Description |
| --- | --- | --- |
| `VITE_API_BASE` | Frontend | Backend base URL used by the dashboard |
| `USE_MODEL` | Backend | Enables remote ML service routing |
| `ML_SERVICE_URL` | Backend | URL of the external ML service |
| `ML_TIMEOUT` | Backend | Timeout for remote ML calls |
| `ALERT_THRESHOLD` | Backend | Minimum toxicity score for alert creation |
| `DISINFO_THRESHOLD` | Backend | Threshold for disinformation / AI media signal |
| `CORS_ORIGINS` | Backend | Allowed frontend origins |
| `SEED_ON_STARTUP` | Backend | Seeds demo data after Render restarts |
| `SAFENET_AI_VIDEO_MODEL` | ML service | Optional override for the video deepfake model |

## Repository Map

```text
backend_api/          FastAPI API, alert storage, WebSocket stream, backend fallback logic
contracts/            Shared Pydantic schemas between services
frontend_dashboard/   Vercel React dashboard and interactive demo UI
ml_service/           Text, image, and video analyzers using HuggingFace models
simulator_and_logic/  Demo conversation simulator and recommendation engine
whatsapp_bridge/      WhatsApp Web proof-of-concept bridge for live message ingestion
```

## Product Vision: WhatsApp Kids

ParAlert is more than a parental-control dashboard. The long-term vision is to prove that a safer messaging standard for children is possible.

Just as YouTube created a dedicated child-safe experience, WhatsApp could support a protected, consent-based, age-aware mode for children. ParAlert demonstrates the core technology behind that idea: real-time context, media safety, calm parent guidance, and escalation only when it is truly needed.

## Important Notes

- The WhatsApp bridge is a hackathon proof of concept. A real product should use consent-based onboarding and official platform APIs where possible.
- Media analysis supports direct image and video file URLs. YouTube page URLs are intentionally not treated as direct downloadable media.
- Model outputs are decision-support signals, not a replacement for human judgment.
- The system is designed to keep working during demos even when external ML services are unavailable.
