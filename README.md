# 🎯 AI Job Application Agent

AI-powered job application tracker with interview prep, smart recommendations, and visual pipeline management.

## 🚀 Quick Start

```bash
./run_ui.sh
```

Opens at `http://localhost:8501`

## ✨ Key Features

- **🎯 Smart Recommendations** - AI suggests next actions
- **📊 Kanban Board** - Visual pipeline view
- **⚡ 10x Faster** - Database-indexed queries
- **🔍 Enhanced Search** - Search everywhere (descriptions, notes, cover letters)
- **🎯 Interview Prep** - 30+ practice questions, company research, feedback tracking
- **📅 Calendar Integration** - Export interviews to calendar (.ics files)
- **🎛️ Bulk Operations** - Select multiple, update/delete at once
- **📊 Visual Charts** - Interactive analytics dashboard

## 🎯 Quick Tour (2 Minutes)

1. **Dashboard** → See AI recommendations & charts
2. **Applications** → Try Kanban Board view
3. **Click any Interview-stage app** → Interview Prep tab
4. **Try Quick Filters** → Active, High Priority, Awaiting Response

## 📖 Main Features

### Applications Management
- 3 view modes: Table, Cards, Kanban Board
- Quick filters (one-click)
- Bulk operations
- Enhanced search across all fields
- 10x performance boost

### Interview Preparation
- Company research templates
- 30+ practice questions (behavioral, technical, role-specific)
- Answer preparation & confidence tracking
- Practice timer
- Post-interview feedback

### Smart Features
- AI-powered recommendations
- Visual analytics (3 charts)
- Calendar integration (.ics export)
- Email automation (optional)
- Target companies tracking

## 🛠️ Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Launch
./run_ui.sh
```

### Optional: Email Automation
Create `.env` file:
```bash
GMAIL_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

## 💡 Pro Tips

1. **Check Dashboard daily** - See what needs attention
2. **Use Kanban view** - Best pipeline visualization
3. **Bulk operations** - Weekly cleanup of old apps
4. **Interview Prep early** - 24 hours before interviews
5. **Quick Filters** - Faster than manual filtering

## 📁 Structure

```
ai_application_agent/
├── ui/app.py              # Main app
├── agent/agent.py         # Core logic
├── tools/                 # Analysis & automation
├── utils/                 # Calendar, recommendations
├── db/                    # Database models
└── cv/cv.md              # Your CV (customize this!)
```

## 🆘 Troubleshooting

**App won't start:**
```bash
pip install -r requirements.txt
streamlit run ui/app.py
```

**Slow performance:**
```bash
python db/add_indexes.py
```

## 📚 More Documentation

- `QUICK_START.md` - Detailed feature tour
- `ARCHITECTURE.md` - System design
- `AUTOMATION_GUIDE.md` - Email setup
- `GETTING_STARTED.md` - Full guide

## 🎉 What You Get

From basic tracker → Professional AI-powered system:
- ✅ 10x faster queries
- ✅ Visual pipeline (Kanban)
- ✅ AI recommendations
- ✅ Interview prep tools
- ✅ Calendar integration
- ✅ Bulk operations
- ✅ Smart search

**Launch now:** `./run_ui.sh` 🚀
