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

### [2026-05-28] CRITICAL: Render deploys the `fs-server` branch, not `main`
**Discovery:** Live backend (safenet-backend-cnmy.onrender.com) served 3 alerts with NO alert_type = pre-v2 code. origin/fs-server (3c1f3ca) matched exactly and is an ancestor of main (main 38 ahead, fs-server 0 ahead) → Render auto-deploys fs-server.
**Action:** Fast-forwarded origin/fs-server → main (non-destructive, 3c1f3ca..5ffc7a9) so the live backend gets the integrated v2 code regardless of which branch Render watches.
**Follow-up (Phase 3):** Retarget the Render service to `main` and retire fs-server → single deploy branch.

### [2026-05-28] ML strategy: HYBRID (keyword in cloud, real models local via ngrok)
**Decision:** Render stays USE_MODEL=false (keyword fallback) for stability / no OOM on 512MB free tier. Real HF models run only on a laptop for the judge pitch, on a Python 3.11/3.12 venv (NOT 3.14 — torch wheels missing), exposed via ngrok; flip USE_MODEL=true + point the frontend at the ngrok URL during the pitch. Do NOT split ML into a MODEL_URL microservice — models are in-process; ngrok-the-whole-backend is equivalent with zero new parts.

### [2026-05-28] Key learning: fact_check has_media trap
fact_check._heuristic treats has_media=True as suspicious on its own. NEVER call check_claim with has_media=True on the live disinfo path, or every photo becomes a fake-news alert. Live disinfo wiring uses has_media=False (text-only); media authenticity is the vision model's separate job.

### [2026-05-28] i18n architecture (he/en)
Dependency-free: src/i18n/translations.js (STRINGS[lang] nested object, parameterized via functions) + I18nContext.jsx (provider sets documentElement.lang/dir, persists localStorage "safenet.lang", honors ?lang= query first) + LanguageToggle.jsx. Components do `const {t,lang,dir,locale}=useI18n()`. Label maps (category/role/severity/escalation) keyed by contract-C enum values. relativeTime uses Intl.RelativeTimeFormat(locale) and clamps future demo timestamps to "now". English mode loads public/mock_data.en.json + DEMO_SCENARIOS.en and skips the live (Hebrew) backend so an English judge sees a wholly English board. Default Hebrew; he=RTL, en=LTR.

### [2026-05-29] Interactive "Try it" analysis + remote ML service architecture
Judge playground: POST /analyze (JSON text+media_url) and /analyze/upload (multipart file) on backend_api/main.py return contracts.AnalyzeResponse (toxicity, category, media NSFW/deepfake, credibility, model_used); toxic/disinfo also saves+broadcasts an alert (pops on dashboard). Heavy ML offloaded via ML_SERVICE_URL: when USE_MODEL=true AND ML_SERVICE_URL set, backend forwards to standalone ml_service/server.py (real models, run on a powerful local box behind ngrok); ANY failure -> in-process keyword fallback (never hard-fails). Render stays light (no torch in-process; _LOCAL_USE_MODEL = USE_MODEL and not ML_SERVICE_URL). Keyword heuristic now bilingual (English+Hebrew, text.lower() match) so English judges aren't met with 0%. vision.analyze_path added for uploads. Frontend TryIt.jsx tab (4th tab, ?tab= deep-link). At pitch: run ml_service/server.py on py3.12 + ngrok, set Render USE_MODEL=true + ML_SERVICE_URL, /health shows ml_routing:true. Verified: keyword e2e + HTTP routing + graceful fallback all green.

## Key Learnings (appended 2026-05-29)
- ML fallback `_heuristic_score` uses SUBSTRING match (`phrase in low`), not word-boundary. Never add short keywords (<=3 chars) or words that are substrings of common benign words. Bombs found: en L/ass/rat/fat, he זונה(→תזונה)/זין(→מגזין)/כוס(→כוסות). Single hit = 0.75 > threshold 0.49.
- Deploy (CORRECTED 2026-05-29): Vercel builds frontend_dashboard/app; Render service "safenet-backend" builds the Python backend from branch `main`. Render AUTO-DEPLOY IS OFF — pushing main does NOT deploy; must Manual Deploy in Render dashboard. fs-server is now force-aligned to main (identical); main is the single authoritative branch.

## Key Learnings (appended 2026-05-29, frontend redesign)
- **Frontend IS now in scope.** Earlier "FS-A, never touch frontend_dashboard" was the hackathon team split. Project is now solo-rebranded ParAlert on `main`; user directly requested frontend redesign. The old off-limits rule no longer applies.
- **Theming is token-driven (Tailwind v4 `@theme`).** Every component uses semantic tokens (ink/surface/surface-2/edge/content/muted/faint/accent/sev-*/victim/aggressor/bystander). Light mode = override these CSS vars under `:root[data-theme="light"]` in index.css — whole UI flips, ~zero component churn. `ink` = page bg.
- **`bg-ink` reused as a recessed surface inverts wrong in light** (ink=page bg). Fixed AlertCard bubbles + Settings inputs/track to `bg-surface-2`. FilterBar inactive count chip -> `bg-edge`.
- **Chat components (ChatSimulator, GroupChat) are self-contained light** — hardcoded bg-white/text-slate-*/emerald (WhatsApp look), NOT token-driven for their panes. Light theme does not break them. User said they're great — DO NOT TOUCH.
- **Theme system:** theme/ThemeContext.jsx (localStorage `paralert.theme`, default dark) + components/ThemeToggle.jsx (segmented, mirrors LanguageToggle). Pre-paint script in index.html avoids flash. `?theme=light|dark` query override.
- **Wide layout without stretching:** dashboard container max-w-5xl, nav is w-fit segmented, alert sections use CSS `lg:columns-2` masonry + `break-inside-avoid` per card. Cards stay readable-width, fill desktop.
- **Font:** added Google "Assistant" (full Hebrew+Latin, RTL-safe) via index.html. Don't use Latin-only fonts (Geist/Inter) — RTL Hebrew-first app.
- **designqc gotcha:** drops multi-param query strings (params after the first `&` lost). Single `?theme=light` survived; `&tab=`/`&lang=` did not apply.
- **vite:** use `npm run build`/`npm run dev`, not `npx vite` (hook rewrites to npm -> "Missing script: vite").

## User Preferences (appended 2026-05-29, design)
- Fully-rounded (rounded-full/2xl) UI reads "AI" to the user. Prefers a **subtle neo-brutalist** lean: sharper radii (cards rounded-lg, inner boxes/badges/buttons rounded-md, tiny pills rounded), crisp hard-edge shadows (`0 2px 0` + small ambient) over big soft floats. Key phrase: "ממש בקטנה" — keep it restrained, NOT zero-radius/thick-black-border full brutalism. Keep dots, meter bars, avatars, switches round.
- Does NOT want a "demo mode" / source-status indicator — removed the header status pill. Says it's not useful.
- designqc (`openwolf designqc --url`) DROPS query strings — `?theme=light` does not reach the SPA, so it always captures the default (dark) theme. md5 diffs between runs are just live-animation noise. To verify a non-default theme, can't rely on designqc query passthrough; theme-independent changes (radii/shadow/layout) are still verifiable from a default-theme capture.
- AlertCard.jsx has CONCURRENT edits from the user/teammate (added EvidenceSection + lib/evidence.js). Re-read before editing; preserve their changes.

## Key Learnings (appended 2026-05-29, no-LLM prod)
- **NO live LLM in production / on stage.** No ANTHROPIC_API_KEY is set. recommendation_engine.generate_recommendation ALWAYS takes the template fallback path in prod. Do NOT add `anthropic` to backend_api/requirements.txt or assume Haiku runs on the demo — the parent "recommendation" is the role-keyed template + escalation suffix. (Pitch says "LLM" but prod is templated.)
- **Escalation is NOT on AnalysisResult.** The analyzer never sets `escalation` (stays "none"); it's computed in backend _build_alert via escalation_from(category, severity). Any code needing escalation from an AnalysisResult must derive it itself (fixed bug-083 in recommendation_engine this way).
- **Keyword heuristic matching rule (text_analyzer._phrase_in):** English keywords = WORD BOUNDARY (re \b) so substrings of benign words don't fire; Hebrew = substring (preserves prefix morphology המטומטם/ולוזר). NEVER add Hebrew homographs (שמן=oil, חמור=severe, מסכן, תינוק, מוזר, שום דבר) or benign-common English single words (baby/joke/ratio/lame/bare nobody) — substring/standalone match = false bullying alert at one hit (0.75 > 0.49). See bug-084.

## Decision Log (appended 2026-05-29)
### [2026-05-29] CODE FREEZE before presentation
System stable, demo works. User froze code pre-presentation to avoid side-effect risk. DO NOT fix the known-but-deferred items: #4 double media analysis (server.py/main.py analyze URL twice), #5 bridge sends media_url "[media]", #6 stale anatomy.md, #7 safenet naming drift. Only break freeze on explicit user request.
### [2026-05-29] Pitch wording: "role-based recommendation engine" (not "live LLM")
Prod has no live LLM (no ANTHROPIC_API_KEY). Narrative: LLM was used BEFOREHAND to generate the decision tree -> zero-latency, offline-stable role-based engine. Verbal/slide change, no code.
