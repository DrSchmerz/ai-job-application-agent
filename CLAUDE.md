# AI Application Agent — Project Guide

## Project
Personal AI-powered job search assistant. Stack: Python, Streamlit, SQLAlchemy, SQLite.
Run with `./run_ui.sh` or `streamlit run ui/app.py`.

## Key files
- `ui/app.py` — All page logic (~2400 lines); every page function lives here
- `ui/utils/state.py` — Session state init and helpers
- `ui/utils/styles.py` — Global CSS (minimal/technical aesthetic)
- `ui/components/tables.py` — Reusable HTML table components
- `ui/config.py` — Colors, status options, constants
- `agent/agent.py` — AI logic (cover letter, fit analysis, CV analysis)
- `tools/` — data_tools, job_analyzer, email_tracker, job_scraper, job_search
- `db/` — SQLAlchemy models, session, target_companies
- `cv/cv.md` — User's CV (source of truth for AI prompts)
- `tasks/todo.md` — Current task plan (read at session start)
- `tasks/lessons.md` — Past mistakes and rules (read at session start)

## Navigation (5 pages)
| Page | Route function | Contents |
|---|---|---|
| 📊 Dashboard | `show_dashboard()` | Stats, pipeline, recent apps |
| 📋 Applications | `show_applications_page()` | My Apps tab + Target Companies tab + Find Jobs tab; "+ New Application" button triggers wizard |
| 📧 Email | `show_email_tracking()` | Scan/update emails, AI analysis, match to apps |
| 📝 CV & Insights | `show_cv_insights(provider)` | Job Insights + CV Analysis + Quick Screen (3 tabs) |
| ⚙️ Settings | `show_settings()` | AI provider, CV, email automation, DB export |

## Session state keys
- `app_view` — `"list"` (default) or `"new_application"` — controls Applications wizard toggle
- `workflow` — dict for multi-step new-application wizard state
- `selected_provider` — active AI provider
- `email_last_scan` / `email_scanned_emails` — email scan cache
- `cv_analysis_result` — cached holistic CV analysis

## UI conventions
- Minimal/technical aesthetic — tight spacing, 1px borders, 4px radius, muted colors
- No gradient backgrounds, no hover transforms, no large shadows
- Font: 14px base, 0.875rem body, 1.4rem h1
- Status badges: small pills (2px 8px padding, 3px radius)
- Scores: small colored badge (not large circles)

## Code conventions
- Page functions are top-level in `ui/app.py`
- Wrapper functions (`show_applications_page`, `show_cv_insights`) call existing page functions — do not modify the inner functions
- `ui/pages/workflow.py` is legacy — no longer imported
- Touch only what is necessary

## Session start checklist
1. Read `tasks/lessons.md`
2. Read `tasks/todo.md`
3. Do not write code until both are read

## Planning
- 3+ step tasks → write plan to `tasks/todo.md`, get approval first
- Simple 1-2 step fix → just do it

## Self-improvement
After any correction → update `tasks/lessons.md` with a rule ("Always X" / "Never Y")
