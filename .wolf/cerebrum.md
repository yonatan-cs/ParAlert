# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-05-28

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

- The user is **FS-A** on branch `fs-server`. Edit ONLY `backend_api/` + `whatsapp_bridge/`. NEVER touch teammate code: `frontend_dashboard/` + `simulator_and_logic/` (FS-B, `fs-dashboard`) or `ml_service/` (ML pair, `ml`). A teammate is actively working on `fs-dashboard`.
- `fetch`/`pull` from origin periodically to stay in sync with teammates; never force-push a shared branch without explicit approval.
- When the user asks to revert commits from the graph, prefer a history rewrite like `git reset --hard` over creating a revert commit.
- If the target commit is the root, use a new root commit or ref rewrite to remove it from the graph instead of trying to reset past it.
- If the user wants zero commits in the graph, convert the branch to an unborn branch and delete all local refs, including remote-tracking refs.

## Key Learnings

- **Project:** Hackathon-Project

- `61aa7ac` is the root commit in this repo; the branch can be moved back to it, but there is no earlier parent to reset behind it.
- A local graph can be re-rooted by creating a new empty root commit with `git commit-tree` and updating branch refs with `git update-ref`.
- An unborn branch with `git symbolic-ref HEAD refs/heads/<name>` and no branch ref results in `git status` showing "No commits yet on <name>".

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

- [2026-05-28] Do not say a root commit can be removed with `git reset` to an earlier parent; if the user wants it out of the graph, re-root the branch instead.
- [2026-05-28] Do not leave remote-tracking refs in place when the user asks for zero commits in the graph; delete them too.
- [2026-05-28] On Windows, do NOT trust `uvicorn --reload` for this project — WatchFiles can log "Reloading..." but never bring up the new worker, leaving the OLD code serving (a WS route 403'd because it wasn't loaded). Run uvicorn WITHOUT `--reload` and restart manually after edits. See bug-008.
- [2026-05-28] `cd whatsapp_bridge && npm install` fails on a flaky network because Puppeteer downloads Chromium. Use `PUPPETEER_SKIP_DOWNLOAD=true` and let index.js use system Chrome/Edge via executablePath. See bug-007.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->

### [2026-05-28] Platform integration: whatsapp-web.js (over Telegram / Facebook / Baileys)
**Context:** A judge required a demo that actually works on at least one real platform, not only a simulator.
**Decision:** Build `whatsapp_bridge/` (Node) using `whatsapp-web.js` — parent scans a QR, our app becomes a WhatsApp linked device, real group messages stream to the backend.
**Why over alternatives:**
- **Telegram Bot API** — technically simplest + zero ban risk, but OFF the product narrative (product is WhatsApp-first). Rejected.
- **Facebook / Messenger (Graph API)** — requires Meta app review + business verification; not feasible in a hackathon. Rejected.
- **Discord** — trivial bot API but wrong audience. Rejected.
- **Baileys** — lighter (websocket, no browser) but higher ban risk + less stable than whatsapp-web.js. Rejected.
- **WhatsApp Business API (official BSP)** — the only ToS-safe path, but too heavy/slow to set up for a demo. Deferred to "real production" note.
**Trade-off accepted:** whatsapp-web.js is unofficial (ToS violation), ban possible within weeks → use a burner/demo number only. Fine for a one-shot demo.
**Architectural consequence:** the bridge emits the exact same **contract A** (`IncomingMessage`) as `simulator_and_logic/simulator.py`. Two interchangeable producers, backend is source-agnostic → ZERO backend change, and the simulator stays as a stage fallback.

### [2026-05-28] WhatsApp bridge drives system Chrome (skip Puppeteer Chromium)
**Decision:** `whatsapp_bridge/index.js` resolves a browser path (`CHROME_PATH` env → auto-detect Chrome/Edge on Windows) and passes it as `puppeteer.executablePath`; install with `PUPPETEER_SKIP_DOWNLOAD=true`.
**Why:** Puppeteer's bundled-Chromium download is large and failed here with ECONNRESET (bug-007). Every Windows dev already has Chrome/Edge, so reusing it is faster and removes a flaky network dependency. Verified the bridge boots Chrome and renders the linked-device QR.

### [2026-05-28] Realtime alert push via WebSocket (additive, polling still works)
**Decision:** Added `GET ws://.../ws/alerts`. `/ingest` stays a sync def (so a blocking LLM recommendation can't stall the event loop) and broadcasts new alerts onto the captured main loop via `asyncio.run_coroutine_threadsafe`. Dashboards may still poll `GET /alerts`.
**Why:** Real-time pop on stage without forcing the frontend off polling; sync /ingest avoids event-loop blocking. FS-B (frontend) can consume `/ws/alerts` when ready.

### [2026-05-28] Backend runtime config via env vars (USE_MODEL, ALERT_THRESHOLD)
**Decision:** `backend_api/main.py` reads `USE_MODEL` (default false → keyword fallback) and `ALERT_THRESHOLD` (default 0.5) from the environment; both are echoed by `GET /health`.
**Why:** On stage we need to flip from the keyword stub to the real HF model and tune the alert threshold without editing/redeploying code. Defaults preserve the safe demo behavior. ML model still loads with its own keyword fallback, so `USE_MODEL=true` never crashes even if transformers/torch are missing.

### [2026-05-28] Contract-first design + 2-pair team split
**Decision:** Lock the 3 JSON contracts in `contracts/schemas.py` (A: incoming msg, B: analysis, C: alert) before writing feature code; everything communicates only through them. Team works as 2 pairs on separate branches: `ml` (`ml_service/`: analyzer.py + role_classifier.py) and `fullstack` (`backend_api/` + `frontend_dashboard/` + `whatsapp_bridge/`).
**Why:** Hackathon-grade zero-friction parallelism — no two people touch the same file. Refactors are expensive under time pressure, so contracts are nailed down first. Pydantic models double as runtime validation + FastAPI Swagger docs.
**Reliability stance:** every external call (ML model, LLM, WhatsApp) is wrapped with a try/except + fallback (keyword heuristic / template recommendation / stub) so the demo never crashes on stage.
