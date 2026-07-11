# 🏗️ Architecture Overview

Visual guide to understand how components connect.

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│  python3 cli/main.py apply                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLI (cli/main.py)                      │
│  • Collect: company, role, job description                  │
│  • Display: Rich tables, prompts, formatted output          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 AGENT (agent/agent.py)                      │
│  1. Load CV summary from data/cv_summary.txt                │
│  2. Load prompt template from prompts/                      │
│  3. Fill template with CV + job details                     │
│  4. Call OpenAI API (GPT-4o-mini)                          │
│  5. Return generated cover letter                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              DATA TOOLS (tools/data_tools.py)               │
│  • Save application to database                             │
│  • Save cover letter to file                                │
│  • Load CV, cover letters, job URLs                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                DATABASE (applications.db)                   │
│  SQLAlchemy ORM → SQLite                                    │
│  Schema: db/models.py                                       │
│  Session: db/session.py                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Complete Flow Example

**User runs:** `python3 cli/main.py apply`

```
1. CLI collects input:
   ├─ Company: "MongoDB"
   ├─ Role: "Solutions Architect"
   └─ Job Description: <pasted text>

2. CLI calls Agent:
   agent.analyze_job_fit(job_description)
   ├─ Loads CV summary
   ├─ Calls OpenAI API
   └─ Returns: {fit_score: 8, strengths: [...], gaps: [...]}

3. CLI shows fit analysis to user

4. User confirms → CLI calls Agent again:
   agent.generate_cover_letter(company, role, job_description)
   ├─ Loads CV summary
   ├─ Loads prompt template
   ├─ Fills template
   ├─ Calls OpenAI API
   └─ Returns: <cover letter text>

5. CLI shows cover letter

6. User approves → CLI calls Data Tools:
   add_application(company, role, ...)
   ├─ Creates Application object
   ├─ Saves to database
   └─ Returns: application record

7. CLI optionally saves cover letter file:
   Path("data/cover_letters/...").write_text(cover_letter)

8. Done! ✅
```

## 📦 Module Dependencies

```
cli/main.py
  ├─ imports → agent/agent.py
  │             └─ imports → prompts/cover_letter_prompt.txt
  │             └─ uses → OpenAI API
  │
  └─ imports → tools/data_tools.py
                └─ imports → db/models.py
                └─ imports → db/session.py
                              └─ creates → applications.db
```

## 🗂️ File Interactions

### When you run `apply`:

**Reads:**
- `data/cv_summary.txt` (your background)
- `prompts/cover_letter_prompt.txt` (template)
- `.env` (OpenAI API key)

**Writes:**
- `applications.db` (new application record)
- `data/cover_letters/Philipp_Goetting_Cover_Letter_<Company>.txt` (if you choose)

### When you run `list`:

**Reads:**
- `applications.db` (query applications)

**Writes:**
- Nothing (read-only)

### When you run `stats`:

**Reads:**
- `applications.db` (count by status)

**Writes:**
- Nothing (read-only)

## 🎨 Component Responsibilities

### 1. CLI (`cli/main.py`)
**Role:** User interface (commands, prompts, display)

**Does:**
- Parse command-line arguments
- Prompt user for input
- Display formatted output (tables, colors)
- Orchestrate calls to agent and tools

**Doesn't:**
- Call OpenAI directly (that's agent's job)
- Access database directly (that's tools' job)
- Store any state

---

### 2. Agent (`agent/agent.py`)
**Role:** AI/LLM interaction logic

**Does:**
- Load CV summary and prompts
- Format prompts with job details
- Call OpenAI API
- Parse and return results

**Doesn't:**
- Interact with user (that's CLI's job)
- Save to database (that's tools' job)
- Know about CLI commands

---

### 3. Data Tools (`tools/data_tools.py`)
**Role:** Data access layer

**Does:**
- Load CV, cover letters, job URLs
- Database CRUD operations
- File I/O for cover letters

**Doesn't:**
- Call OpenAI (that's agent's job)
- Display to user (that's CLI's job)
- Know about prompts

---

### 4. Database (`db/`)
**Role:** Data persistence

**Files:**
- `models.py` - Define schema (Application class)
- `session.py` - Database connection config
- `applications.db` - SQLite database file

**Does:**
- Store application records
- Provide query interface via SQLAlchemy

**Doesn't:**
- Generate cover letters
- Display data
- Call APIs

---

### 5. Prompts (`prompts/`)
**Role:** AI prompt templates

**Does:**
- Define structure for LLM requests
- Use `{placeholders}` for dynamic content

**Doesn't:**
- Execute (agent does that)
- Store data
- Call APIs

---

## 🔌 Extension Points

Want to add features? Here's where:

### Add a new CLI command
**File:** `cli/main.py`
```python
@app.command()
def mycommand():
    # Your code here
```

### Add a new data tool
**File:** `tools/data_tools.py`
```python
def my_tool():
    # Your code here
```

### Add a new agent capability
**File:** `agent/agent.py`
```python
def my_method(self):
    # Your code here
```

### Add a new prompt template
**File:** `prompts/my_prompt.txt`
Then load in agent:
```python
template = self._load_prompt_template("my_prompt.txt")
```

### Add a new database field
**File:** `db/models.py`
```python
class Application(Base):
    # Add new column
    my_field = Column(String)
```
Then recreate database.

---

## 🧪 Testing Strategy

### Test individual components:

```bash
# Test agent
PYTHONPATH=. python3 agent/agent.py

# Test data tools
PYTHONPATH=. python3 tools/data_tools.py

# Test database
PYTHONPATH=. python3 -c "from db.session import init_db; init_db()"
```

### Test CLI commands:

```bash
python3 cli/main.py --help
python3 cli/main.py list
python3 cli/main.py stats
python3 cli/main.py apply  # Interactive
```

### Test database queries:

```bash
PYTHONPATH=. python3 -c "
from tools.data_tools import get_applications, get_application_stats
print(get_applications())
print(get_application_stats())
"
```

---

## 🎯 Key Design Decisions

### 1. Separation of Concerns
Each module has ONE job:
- CLI = Interface
- Agent = AI logic
- Tools = Data access
- DB = Persistence

**Why:** Easy to test, modify, and extend independently.

---

### 2. Simple Over Complex
- No framework overkill (Django, FastAPI)
- Plain SQLite, not PostgreSQL
- Typer CLI, not complex argparse
- Direct OpenAI calls, not LangChain (for now)

**Why:** Easier to understand and maintain. Add complexity only when needed.

---

### 3. Local-First
- All data in SQLite file
- CV and cover letters as local files
- No cloud storage

**Why:** Privacy, speed, no vendor lock-in.

---

### 4. API Efficiency
- Use `gpt-4o-mini` (cheap, fast)
- Don't call API unnecessarily
- Retry logic with tenacity (installed)

**Why:** Save money, faster responses.

---

### 5. User in Control
- Always show AI output before saving
- Confirm before saving to database
- Edit before committing

**Why:** Trust but verify. You're the human.

---

## 🔮 Future Architecture

As project grows, consider:

### Phase 3-4: Add Layers
```
Presentation Layer (UI)
  ├─ Streamlit UI
  └─ CLI

Business Logic Layer (Agent)
  ├─ Application agent
  ├─ Email scanner
  └─ Job matcher

Data Access Layer (Tools)
  ├─ Data tools
  ├─ Web scraper
  └─ File tools

Persistence Layer (DB)
  └─ SQLite/PostgreSQL
```

### Phase 5-6: Add Services
```
Core App
  ├─ API Server (FastAPI)
  │   └─ REST endpoints
  ├─ Background Tasks (Celery)
  │   └─ Scheduled jobs
  └─ Queue (Redis)
      └─ Job processing
```

But for now, **keep it simple**! 🚀
