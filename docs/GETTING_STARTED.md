# 🚀 Getting Started - AI Application Agent

Welcome to your AI-powered job application assistant! This guide will help you understand what we've built and how to continue developing it.

## ✅ What We Built (MVP)

A **functional prototype** with:

1. **Database tracking** (SQLite + SQLAlchemy)
2. **AI Agent** (OpenAI integration for cover letter generation)
3. **CLI Interface** (4 working commands)
4. **Data management** (Your CV, cover letters, and job URLs organized)
5. **Prompt templates** (For cover letter generation)

---

## 🎯 Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key with credits (add credits at platform.openai.com)
- Virtual environment activated

### Setup (Already Done)
```bash
# Your environment is already set up, but for reference:
pip install -r requirements.txt
```

### Update Your CV Summary
**IMPORTANT:** Before using the agent, update your CV summary:

```bash
# Edit this file with your actual background:
nano data/cv_summary.txt
```

Add your:
- Professional background (3-5 sentences)
- Key technical and business skills
- Notable achievements
- Languages spoken

---

## 🖥️ CLI Commands

### 1. Apply to a Job (Main Feature)
```bash
python3 cli/main.py apply
```

**What it does:**
1. Asks for company name, role, job URL (optional)
2. Prompts you to paste the job description
3. **Analyzes your fit** for the role (score 1-10, strengths, gaps)
4. **Generates a tailored cover letter** using AI
5. Shows you the cover letter
6. Saves to database if you approve
7. Optionally saves cover letter file

**Example:**
```bash
python3 cli/main.py apply --company "MongoDB" --role "Solutions Architect"
# Then paste job description and press Ctrl+D
```

### 2. List Your Applications
```bash
python3 cli/main.py list
```

**Options:**
```bash
# Filter by status
python3 cli/main.py list --status "Applied"

# Limit results
python3 cli/main.py list --limit 5
```

### 3. View Statistics
```bash
python3 cli/main.py stats
```

Shows counts of applications by status (Applied, Interview, Rejected, etc.)

### 4. Launch UI (Future)
```bash
python3 cli/main.py ui
```

Launches the Streamlit UI (needs implementation - see roadmap below)

---

## 📁 Project Structure

```
ai_application_agent/
│
├── agent/                      # AI Agent logic
│   └── agent.py               # ApplicationAgent class (OpenAI integration)
│
├── tools/                     # Utility functions
│   └── data_tools.py         # CV/cover letter/database tools
│
├── db/                        # Database layer
│   ├── models.py             # SQLAlchemy Application model
│   └── session.py            # Database session config
│
├── prompts/                   # AI prompt templates
│   └── cover_letter_prompt.txt  # Cover letter generation prompt
│
├── cli/                       # Command-line interface
│   └── main.py               # Typer CLI with all commands
│
├── ui/                        # Streamlit UI (stub)
│   └── app.py                # UI app (needs implementation)
│
├── data/                      # Your data
│   ├── cv/                   # Your CV (PDF)
│   ├── cv_summary.txt        # CV summary for AI (FILL THIS IN!)
│   ├── cover_letters/        # Generated/saved cover letters
│   └── job_urls.txt          # 16 job URLs extracted from Excel
│
├── applications.db            # SQLite database
├── .env                      # OpenAI API key (keep private!)
└── main.py                   # Main entry point (empty for now)
```

---

## 🧩 How Components Work

### Database Schema
```python
class Application:
    id                 # Auto-generated
    company            # "MongoDB"
    role               # "Solutions Architect"
    job_url            # Link to job posting
    status             # "Applied" | "Interview" | "Rejected" | "Offer"
    application_date   # When applied (auto-set)
    cv_used            # Path to CV file used
    cover_letter       # Path to cover letter file
    last_contact       # For follow-ups
    notes              # Your notes
```

### Agent Flow
1. **Load CV summary** from `data/cv_summary.txt`
2. **Load prompt template** from `prompts/cover_letter_prompt.txt`
3. **Fill template** with CV + job description
4. **Call OpenAI API** (GPT-4o-mini for cost efficiency)
5. **Return generated cover letter**

### Data Tools
All available in `tools/data_tools.py`:

```python
# CV
load_cv_path()              # Get path to your CV
load_cv_content()           # Load CV as bytes

# Cover letters
list_cover_letters()        # List all cover letters
get_cover_letter_for_company("MongoDB")  # Find by company

# Job URLs
load_job_urls()             # Load 16 URLs from file

# Database
add_application(...)        # Add new application
get_applications(status="Applied")  # Query applications
get_application_stats()     # Get statistics
```

---

## 🗺️ Development Roadmap

Here's what to build next, organized from **simple → complex**:

### Phase 1: Core Improvements (Easy)
**These are small, focused tasks - pick any to start:**

- [ ] **Update CV Summary** - Fill in `data/cv_summary.txt` with your actual background
- [ ] **Add OpenAI credits** - Add $5-10 to test cover letter generation
- [ ] **Customize prompts** - Edit `prompts/cover_letter_prompt.txt` to match your style
- [ ] **Add more statuses** - Update `get_application_stats()` to track "Phone Screen", "Technical", etc.
- [ ] **CLI improvements**:
  - [ ] Add `view` command to show details of one application
  - [ ] Add `update` command to change status
  - [ ] Add `delete` command to remove applications
  - [ ] Add `search` command to search by keywords

### Phase 2: Job Description Fetching (Medium)
**Goal:** Auto-fetch job descriptions from URLs

- [ ] **Install BeautifulSoup/Playwright** for web scraping
- [ ] **Create `fetch_jd()` tool** in `tools/web_tools.py`:
  - Takes URL → Returns job description text
  - Handle different job board formats (Greenhouse, Workday, etc.)
- [ ] **Update `apply` command** to optionally fetch from URL instead of pasting
- [ ] **Respect robots.txt** - Don't scrape sites that prohibit it

**New CLI usage:**
```bash
python3 cli/main.py apply --url "https://stripe.com/jobs/listing/..."
# Auto-fetches JD from URL!
```

### Phase 3: Streamlit UI (Medium)
**Goal:** Visual interface for managing applications

Build out `ui/app.py` with pages:

- [ ] **Page 1: Dashboard**
  - Application stats (cards/charts)
  - Recent applications table
  - Quick actions (apply, view)

- [ ] **Page 2: Applications List**
  - Filterable/sortable table
  - Click to view details
  - Update status inline

- [ ] **Page 3: New Application**
  - Form to paste JD or enter URL
  - Generate cover letter button
  - Preview and edit before saving

- [ ] **Page 4: Cover Letter Preview**
  - View generated cover letter
  - Edit and regenerate
  - Export as PDF/DOCX

**Tech Stack:**
- Streamlit for UI
- Plotly/Altair for charts
- Pandas for data display

### Phase 4: Scheduler (Medium-Hard)
**Goal:** Automated job scanning

- [ ] **Email integration** - Connect to your email inbox (IMAP)
- [ ] **Job alert parser** - Extract job links from LinkedIn/Indeed emails
- [ ] **APScheduler setup** - Run checks every N hours
- [ ] **Notification system** - Alert you about new matches

**Files to create:**
```
scheduler/
  ├── email_scanner.py    # Read inbox for job alerts
  ├── job_parser.py       # Extract job links from emails
  └── scheduler.py        # APScheduler configuration
```

### Phase 5: Advanced AI Features (Hard)
**Goal:** Smarter agent with more capabilities

- [ ] **Resume tailoring** - Generate custom CV versions per job
- [ ] **Interview prep** - Generate practice questions based on JD
- [ ] **Follow-up generator** - Auto-generate follow-up emails
- [ ] **Job matching** - Score jobs from `job_urls.txt` by fit
- [ ] **Multi-model support** - Add Grok, Claude, or local LLMs
- [ ] **RAG for cover letters** - Use your old cover letters as examples

**Advanced prompt templates:**
```
prompts/
  ├── cover_letter_prompt.txt     ✅ Done
  ├── jd_analysis_prompt.txt      # Analyze job requirements
  ├── resume_tailor_prompt.txt    # Tailor CV bullets
  ├── interview_prep_prompt.txt   # Generate practice questions
  └── follow_up_prompt.txt        # Follow-up email templates
```

### Phase 6: Professional Features (Advanced)
**Goal:** Production-ready features

- [ ] **Export to PDF/DOCX** - Convert cover letters to proper formats
- [ ] **LinkedIn integration** - Auto-apply via LinkedIn
- [ ] **Application tracking** - Set reminders for follow-ups
- [ ] **Analytics dashboard** - Track success rate, response time, etc.
- [ ] **Multi-user support** - If you want to share with friends
- [ ] **Docker deployment** - Easy setup for others

---

## 🎓 Learning Path

### If You Want to Learn...

**Python & Backend:**
- Study `agent/agent.py` - See how to structure a class, call APIs
- Study `tools/data_tools.py` - Learn database queries with SQLAlchemy
- Study `cli/main.py` - Learn CLI building with Typer

**AI/LLM:**
- Study `prompts/cover_letter_prompt.txt` - Learn prompt engineering
- Experiment with temperature, max_tokens in `agent.py`
- Try different models (gpt-4, gpt-3.5-turbo, gpt-4o)

**Frontend/UI:**
- Study Streamlit docs: https://docs.streamlit.io
- Check out `ui/app.py` - Basic Streamlit structure
- Learn Plotly for charts: https://plotly.com/python/

**Database:**
- Study `db/models.py` - Learn SQLAlchemy ORM
- Learn migrations: https://alembic.sqlalchemy.org
- Study indexes, relationships, constraints

---

## 🐛 Known Issues

1. **OpenAI API quota exceeded** - Add credits to your account
2. **CV summary is placeholder** - Update `data/cv_summary.txt` with your info
3. **UI is stub** - Only shows navigation, no functionality yet
4. **No web scraping** - Must paste job descriptions manually
5. **No scheduler** - No automated job scanning yet

---

## 💡 Pro Tips

1. **Start small** - Pick ONE feature from Phase 1 and implement it fully
2. **Test as you go** - Run commands after each change
3. **Use version control** - Commit after each working feature:
   ```bash
   git init
   git add .
   git commit -m "Add view command to CLI"
   ```
4. **Read the code** - Best way to learn is to modify existing functions
5. **Don't over-engineer** - Keep it simple, ship working features
6. **Ask for help** - Use this assistant when you get stuck!

---

## 🔧 Common Tasks

### Add a new CLI command
1. Open `cli/main.py`
2. Add a new function with `@app.command()` decorator
3. Use Rich for pretty output
4. Test with `python3 cli/main.py <command>`

### Add a new prompt template
1. Create file in `prompts/` (e.g., `interview_prep_prompt.txt`)
2. Use `{placeholders}` for dynamic content
3. Load in agent with `_load_prompt_template()`
4. Add new method to `ApplicationAgent` class

### Update database schema
1. Edit `db/models.py` - Add column to `Application` class
2. Delete `applications.db`
3. Run: `PYTHONPATH=. python3 -c "from db.session import init_db; init_db()"`
4. Database recreated with new schema

### Add a new data tool
1. Open `tools/data_tools.py`
2. Add new function with docstring
3. Use type hints
4. Test with `PYTHONPATH=. python3 tools/data_tools.py`

---

## 📞 Getting Help

When you get stuck:

1. **Read error messages** - They usually tell you what's wrong
2. **Check imports** - Use `PYTHONPATH=.` when running scripts
3. **Test in isolation** - Run individual functions with `if __name__ == "__main__"`
4. **Use the assistant** - Describe what you're trying to do and what error you got
5. **Check documentation**:
   - OpenAI: https://platform.openai.com/docs
   - Typer: https://typer.tiangolo.com
   - SQLAlchemy: https://docs.sqlalchemy.org
   - Streamlit: https://docs.streamlit.io

---

## 🎉 You're Ready!

Your prototype is functional. Now pick a feature from the roadmap that interests you and start building!

**Suggested first task:** Update `data/cv_summary.txt` with your real background, add OpenAI credits, then try:

```bash
python3 cli/main.py apply
```

Have fun building! 🚀
