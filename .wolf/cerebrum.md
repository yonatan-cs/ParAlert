# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-05-28

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

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

### [2026-05-28] Contract-first design + 2-pair team split
**Decision:** Lock the 3 JSON contracts in `contracts/schemas.py` (A: incoming msg, B: analysis, C: alert) before writing feature code; everything communicates only through them. Team works as 2 pairs on separate branches: `ml` (`ml_service/`: analyzer.py + role_classifier.py) and `fullstack` (`backend_api/` + `frontend_dashboard/` + `whatsapp_bridge/`).
**Why:** Hackathon-grade zero-friction parallelism — no two people touch the same file. Refactors are expensive under time pressure, so contracts are nailed down first. Pydantic models double as runtime validation + FastAPI Swagger docs.
**Reliability stance:** every external call (ML model, LLM, WhatsApp) is wrapped with a try/except + fallback (keyword heuristic / template recommendation / stub) so the demo never crashes on stage.
