# 🎯 AI Job Application Agent

An AI-powered assistant that manages a full job search end-to-end: track applications,
generate tailored cover letters, analyse job–CV fit, ingest and classify recruiter
emails, and prepare for interviews — all from one local Streamlit app.

Built as a personal project to explore multi-provider LLM orchestration, the
[Model Context Protocol (MCP)](https://modelcontextprotocol.io), and a clean
data layer around a real-world workflow.

> **Privacy note:** this repo ships **no personal data**. Your applications,
> cover letters, CV and API keys live in git-ignored files. A one-command demo
> seeds realistic **fake** data so you can try it immediately.

---

## ✨ Features

- **Multi-provider AI** — Groq, Google Gemini, OpenAI, with an offline keyword
  fallback and an `auto` mode that picks the best available provider.
- **Cover-letter generation** tailored to a job description + your CV summary.
- **Job–CV fit analysis** — score, matched skills, gaps, recommendation.
- **Application tracker** — SQLite-backed, with a full change-history audit trail.
- **Email intelligence** — scan a Gmail inbox, classify messages
  (rejection / interview / offer / scheduling) with an LLM, and auto-update statuses.
- **Interview prep** — practice questions, company research, feedback tracking.
- **Calendar export** — interviews to `.ics`.
- **MCP server** — exposes the agent's tools over the Model Context Protocol.
- **Streamlit UI** — Dashboard, Applications (table / cards / kanban), Email,
  CV & Insights, Settings.

## 🏗️ Architecture

```
┌────────────┐     ┌──────────────────┐     ┌───────────────────────────────┐
│ Streamlit  │────▶│ ApplicationAgent │────▶│ LLM providers                 │
│ UI (ui/)   │     │ (agent/)         │     │ groq · gemini · openai · local│
└─────┬──────┘     └──────┬───────────┘     └───────────────────────────────┘
      │                   │
      ▼                   ▼
┌────────────┐     ┌──────────────────┐     ┌──────────────┐
│ tools/     │     │ db/ (SQLAlchemy) │────▶│ SQLite       │
│ email·jobs │     │ models·session   │     │ applications │
└────────────┘     └──────────────────┘     └──────────────┘
      ▲
      │
┌────────────┐
│ mcp_server/│  Model Context Protocol tools
└────────────┘
```

## 🚀 Quick start

```bash
# 1. Create the environment (Python 3.13)
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure secrets
cp .env.example .env         # then add your API keys (all optional; "local" needs none)

# 3a. Try it with demo data (recommended first run)
python scripts/seed_demo_data.py
APP_DB_PATH=applications_demo.db streamlit run ui/app.py

# 3b. …or run against your own data
cp data/cv_summary.example.txt data/cv_summary.txt   # then edit with your CV
./run_ui.sh
```

App opens at http://localhost:8501.

## ⚙️ Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` / `GROQ_API_KEY` / `GOOGLE_API_KEY` | LLM providers (any subset) |
| `DEFAULT_LLM_PROVIDER` | `local` \| `groq` \| `google` \| `openai` \| `auto` |
| `GMAIL_EMAIL` / `GMAIL_APP_PASSWORD` | optional Gmail integration (use an App Password) |
| `APP_DB_PATH` | SQLite file to use (defaults to `applications.db`) |

## 📁 Project layout

```
agent/        Multi-provider AI agent (cover letters, fit analysis)
ui/           Streamlit app — page functions + components
tools/        Email tracking/analysis, job scraping & search
db/           SQLAlchemy models, session, migrations
mcp_server/   MCP server exposing agent tools
scripts/      Utilities (e.g. seed_demo_data.py)
cli/          Command-line interface
data/         Local data (git-ignored; *.example.* files are shipped)
```

## 🛠️ Tech stack

Python 3.13 · Streamlit · SQLAlchemy + SQLite · OpenAI / Groq / Google Gemini SDKs ·
Model Context Protocol · pandas · scikit-learn

## 🗺️ Roadmap

- [ ] Unify provider logic behind a single `LLMProvider` interface
- [ ] Structured logging (replace prints) + `pytest` test suite + CI
- [ ] Migrate `google-generativeai` → `google-genai`
- [ ] Dockerfile + Compose for one-command run and deployment
- [ ] Semantic (embedding-based) job–CV fit scoring

## 📄 License

[MIT](LICENSE) © 2026 Philipp Goetting
