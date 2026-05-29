# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-29T02:28:11.834Z
> Files: 40 tracked | Anatomy hits: 0 | Misses: 0

## ../../../../../../../tmp/

- `safenet_phase1.py` — Phase 1 verification: live disinformation wiring + WS hardening. (~1037 tok)
- `safenet_smoke.py` — SafeNet end-to-end smoke test (use_model=False / keyword path). (~945 tok)

## ../../Users/netan/.claude/projects/c--Hackathon-Project-Hackathon-Project/memory/

- `feedback_file_ownership.md` — Declares signatures (~360 tok)
- `feedback_git_workflow.md` (~441 tok)
- `MEMORY.md` — Memory Index (~75 tok)

## ./

- `DEPLOY.md` — 🚀 DEPLOY — SafeNet חי לשופטים (~2002 tok)
- `README.md` — Project documentation (~555 tok)
- `render.yaml` — Render Blueprint for the ParAlert backend (FS-A). (~449 tok)

## .claude/


## .claude/rules/


## .wolf/


## backend_api/

- `_review.py` — Live review driver for FS-A: drives every endpoint + WS through the real socket, plus probes. (~1331 tok)
- `main.py` — API: 6 endpoints (~5802 tok)
- `requirements.txt` — Python dependencies (~23 tok)

## contracts/

- `schemas.py` — Pydantic: IncomingMessage (~1333 tok)

## frontend_dashboard/


## frontend_dashboard/app/

- `index.html` — ParAlert (~382 tok)

## frontend_dashboard/app/public/

- `mock_data.en.json` (~2484 tok)

## frontend_dashboard/app/src/

- `App.jsx` — Backend base is env-driven for deploy (Vercel sets VITE_API_BASE to the hosted (~3192 tok)
- `index.css` — Styles: 14 rules, 34 vars (~1133 tok)
- `main.jsx` (~162 tok)

## frontend_dashboard/app/src/components/

- `AlertCard.jsx` — SEV (~2075 tok)
- `ChatSimulator.jsx` — WhatsApp-Web-style scripted demo: a vertical group list (sidebar) + the selected (~2168 tok)
- `FilterBar.jsx` — FILTER_KEYS (~345 tok)
- `GroupChat.jsx` — A persistent, interactive WhatsApp-style group chat docked beside the dashboard. (~3350 tok)
- `LanguageToggle.jsx` — Compact EN / עב segmented switch. dir="ltr" so the order is stable in both layouts. (~235 tok)
- `Settings.jsx` — SENS (~1631 tok)
- `SummaryBar.jsx` — At-a-glance: the 3 bullying angles + the two new dimensions (police-severe, disinfo). (~604 tok)
- `ThemeToggle.jsx` — Compact light/dark segmented switch — same visual language as LanguageToggle. (~283 tok)
- `TryIt.jsx` — Interactive playground: judges submit text / media URL / a file and get a live (~2108 tok)

## frontend_dashboard/app/src/data/

- `demoChat.js` — Multi-group demo scenarios for the chat opener ("Play"), per language. (~1596 tok)

## frontend_dashboard/app/src/i18n/

- `I18nContext.jsx` — Lightweight, dependency-free i18n. `lang` drives both the string table and the (~467 tok)
- `translations.js` — All UI strings for ParAlert, per locale. `useI18n().t` returns one of these objects. (~3037 tok)

## frontend_dashboard/app/src/lib/

- `evidence.js` — Client-side "evidence package" for severe (police) alerts. Renders the alert's (~1730 tok)
- `format.js` — Locale-aware relative time. Intl.RelativeTimeFormat gives correct grammar in (~264 tok)

## frontend_dashboard/app/src/settings/

- `SettingsContext.jsx` — Shared, persisted parent settings. Both the dashboard (App) and the Settings tab (~1016 tok)

## frontend_dashboard/app/src/theme/

- `ThemeContext.jsx` — Dependency-free light/dark theme. `theme` drives documentElement[data-theme], (~441 tok)

## ml_service/

- `requirements.txt` — Python dependencies (~57 tok)
- `role_classifier.py` — classify_category, classify_role (~650 tok)
- `RUN_LOCAL.md` — 🤖 הרצת המודלים האמיתיים מקומית (ML service + Cloudflare Tunnel) (~1311 tok)
- `server.py` — API: 3 endpoints (~1793 tok)
- `text_analyzer.py` — from: analyze, score_text (~3580 tok)
- `vision.py` — from: load, download, score_path, score_path + 4 more (~4025 tok)

## simulator_and_logic/

- `recommendation_engine.py` — generate_recommendation (~1378 tok)

## simulator_and_logic/conversations/


## whatsapp_bridge/

