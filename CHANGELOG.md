# Changelog

All notable changes and feature progress tracked here.

## Current Version

**Version**: v0.8.1 (Clean & Polished)
**Status**: 78% feature complete
**Last Updated**: 2026-02-10

---

## ✅ Implemented Features

### Application Tracking
- [x] Add/edit/delete applications
- [x] Track status (Draft → Applied → Interview → Offer → Accepted/Rejected)
- [x] Store job description, URL, notes
- [x] Calculate fit scores (keyword + AI matching)
- [x] Categorize by role type and seniority
- [x] Application history/timeline with events
- [x] Search and filter applications (status, company, role)
- [x] Sort by date/score/company
- [x] Export to CSV
- [x] Pagination (configurable items per page)
- [x] Table and card views
- [x] Inline editing (status, notes)
- [x] Expandable details with tabs
- [x] Quick actions (save, delete, view)

### Email Integration
- [x] Gmail IMAP connection
- [x] Scan for application emails
- [x] Display email list (sender, subject, date, preview)
- [x] Link emails to applications (manual)
- [x] Auto-link emails (match by company name)
- [x] Bulk email operations (select multiple, link all)
- [x] Email filtering (linked/unlinked/selected)
- [x] Email archiving (remove from list)
- [x] Email preview in expandable cards
- [x] Timeline view (history + emails chronologically)
- [x] Email count per application
- [x] Auto-scheduled email scanning (background thread)
- [x] Configurable scan interval (15/30/60/120 minutes)
- [x] Manual scan trigger
- [x] Auto-match emails to applications

### UI/UX
- [x] Clean professional design
- [x] Dashboard with metrics
- [x] Applications page with table/card views
- [x] Job Insights page (batch analysis)
- [x] Email Tracking page (AI-powered)
- [x] New Application wizard (5 steps)
- [x] Quick Screen page (fast local analysis)
- [x] Settings page
- [x] Sidebar navigation (7 pages)
- [x] Pagination controls
- [x] Expandable details
- [x] Status badges and score indicators
- [x] Light theme with high contrast
- [x] Progress indicators
- [x] Loading states

### Analytics
- [x] Total/Applied/Interview/Offer/Rejected counts
- [x] Response rate calculation
- [x] Average days active
- [x] Fit score average
- [x] Status distribution bar chart
- [x] Score distribution bar chart

### AI Features
- [x] Cover letter generation (OpenAI/Groq/Google)
- [x] Fit analysis (keyword + AI with scoring 1-10)
- [x] Strength/gap identification
- [x] Role categorization (Sales Engineer, Solution Architect, etc.)
- [x] Seniority detection (Junior, Mid, Senior)
- [x] CV suggestions per application
- [x] Batch analysis (analyze all applications at once)
- [x] Email classification (interview/rejection/offer/etc.)
- [x] Email content analysis with AI

---

### Email Intelligence
- [x] Email content parsing (extract interview dates, times, locations)
- [x] Email classification (interview invite, rejection, offer, generic)
- [x] Auto status updates (email content → change application status)
- [x] Interview date/time extraction
- [ ] Entity extraction (names, companies, locations)
- [ ] Attachment download/viewing
- [ ] Email threading (group conversations)

### Notifications & Alerts
- [x] Desktop notifications (important emails)
- [x] Email alerts (new interviews, offers)
- [x] Auto status update notifications
- [ ] Follow-up reminders (7, 14, 30 day)
- [ ] Deadline tracking
- [ ] Interview reminders

## ❌ Not Yet Implemented

### Email Actions (HIGH PRIORITY)
- [ ] Reply from UI
- [ ] Email templates (accept interview, ask questions, follow up)
- [ ] Send follow-up emails
- [ ] Mark as read/unread
- [ ] Flag important
- [ ] Scheduled sending

### Calendar Integration (MEDIUM PRIORITY)
- [ ] Google Calendar sync
- [ ] Create events from interview emails
- [ ] Calendar event reminders
- [ ] Outlook Calendar support
- [ ] iCal export

### Application Intelligence (MEDIUM PRIORITY)
- [ ] Auto-fetch job description from URL
- [ ] Company research (Glassdoor, LinkedIn data)
- [ ] Skills gap analysis
- [ ] Salary data integration (levels.fyi, Glassdoor)
- [ ] Similar role recommendations
- [ ] Application deadline tracking

### Interview Prep (MEDIUM PRIORITY)
- [ ] Per-application prep notes
- [ ] Common interview questions database
- [ ] Company-specific prep materials
- [ ] Mock interview timer
- [ ] Interview feedback tracker
- [ ] Questions to ask employer

### Contact Tracking (MEDIUM PRIORITY)
- [ ] Track recruiters/interviewers
- [ ] Contact notes and interactions
- [ ] Referral tracking
- [ ] Relationship strength scoring
- [ ] LinkedIn profile links
- [ ] Follow-up reminders for contacts

### Document Management (MEDIUM PRIORITY)
- [ ] Multiple CV versions
- [ ] Cover letter templates/library
- [ ] File attachments to applications
- [ ] Version history
- [ ] Auto-backup to cloud
- [ ] Portfolio/work samples links

### Advanced Analytics (LOW PRIORITY)
- [ ] Time series charts (applications over time)
- [ ] Funnel visualization (Applied → Interview → Offer)
- [ ] Success rate by role type
- [ ] Response time analysis
- [ ] Geographic breakdown
- [ ] Company size correlation
- [ ] Weekly/monthly reports
- [ ] Trend predictions

### Automation
- [x] Auto-scan emails on schedule
- [x] Background email sync
- [x] Smart status suggestions
- [x] Configurable automation settings
- [ ] Webhook integrations (Slack, Discord)
- [ ] IFTTT/Zapier connectors
- [ ] Auto-follow-up after N days

### Integration (LOW PRIORITY)
- [ ] LinkedIn job scraping
- [ ] Indeed integration
- [ ] Glassdoor data
- [ ] levels.fyi salary data
- [ ] Trello export
- [ ] Notion export
- [ ] API for external tools

### UI/UX Enhancements (LOW PRIORITY)
- [ ] Keyboard shortcuts
- [ ] Dark mode toggle
- [ ] Customizable dashboard
- [ ] Drag & drop widgets
- [ ] Mobile responsive
- [ ] Offline mode
- [ ] Progressive web app
- [ ] Undo/redo

### Data Management (LOW PRIORITY)
- [ ] Bulk import (CSV, Excel)
- [ ] Bulk edit multiple applications
- [ ] Duplicate detection
- [ ] Data validation
- [ ] PDF export
- [ ] Excel export
- [ ] JSON backup/restore

---

## 📊 Feature Completion

| Category | Complete | Total | % |
|----------|----------|-------|---|
| **Application Tracking** | 9 | 12 | 75% |
| **Email Scanner** | 15 | 15 | 100% |
| **Email Intelligence** | 4 | 7 | 57% |
| **Notifications** | 3 | 5 | 60% |
| **Email Actions** | 0 | 6 | 0% |
| **Calendar** | 0 | 5 | 0% |
| **Application Intel** | 0 | 6 | 0% |
| **Interview Prep** | 0 | 6 | 0% |
| **Contact Tracking** | 0 | 6 | 0% |
| **Documents** | 0 | 6 | 0% |
| **Advanced Analytics** | 0 | 8 | 0% |
| **Automation** | 4 | 7 | 57% |
| **Integration** | 0 | 7 | 0% |
| **UI/UX** | 8 | 16 | 50% |
| **Data Management** | 1 | 7 | 14% |
| **TOTAL** | **88** | **120** | **73%** |

---

## 🎯 Roadmap

### Sprint 1: Email Intelligence (Next 2 weeks)
**Goal**: Make emails actually useful

- [ ] Email content parsing with AI
- [ ] Auto-detect email type (interview/rejection/offer)
- [ ] Extract interview dates/times automatically
- [ ] Auto-update application status from emails
- [ ] Desktop notifications for important emails

### Sprint 2: Calendar & Reminders (Weeks 3-4)
**Goal**: Never miss an interview

- [ ] Google Calendar integration
- [ ] Auto-create events from interview emails
- [ ] Follow-up reminders (7, 14, 30 days)
- [ ] Interview prep alerts
- [ ] Deadline tracking

### Sprint 3: Application Intelligence (Month 2)
**Goal**: Work smarter, not harder

- [ ] Auto-fetch job descriptions from URLs
- [ ] Company research auto-pull
- [ ] Skills gap analysis
- [ ] Salary data integration
- [ ] Interview prep module

### Sprint 4: Advanced Features (Month 3)
**Goal**: Professional-grade tool

- [ ] LinkedIn integration
- [ ] Contact/networking tracker
- [ ] Multiple CV versions
- [ ] Advanced analytics dashboard
- [ ] Email reply from UI

---

## 🐛 Known Issues

1. **Email links not persistent** - Lost on app restart (not saved to database)
2. **No pagination** - Large email lists can be slow
3. **Manual email refresh** - No auto-scan on schedule
4. **No undo** - Can't undo archive/unlink actions
5. **Email sync** - Doesn't mark emails as read in Gmail

---

## 🔄 Recent Changes

### 2026-02-10 - Code Cleanup & Polish (v0.8.1)
- **Code Quality Improvements**
  - Reduced code duplication: -120 lines from app.py
  - Created reusable table components (`ui/components/tables.py`)
  - Consolidated design system in `ui/config.py`
  - Added typography scale, spacing system, shadows
  - Utility functions for consistent colors
- **Database Cleanup**
  - Fixed 9 data quality issues
  - Corrected company name typos (Anthropic, Deloitte, HubSpot, etc.)
  - Fixed invalid status values
  - Cleaned malformed role data
- **File Organization**
  - Removed unused backup files
  - Created `/ui/components/` directory
  - Better separation of concerns
- **Visual Consistency**
  - All tables use same component
  - Consistent spacing (8px grid system)
  - Centralized color definitions
  - Professional, cohesive design

### 2026-02-10 - Web Scraping & Target Companies (v0.8.0)
- **NEW: Job Web Scraper**
  - Auto-fetch job descriptions from URLs
  - Supports LinkedIn, Indeed, Greenhouse, Lever, generic websites
  - One-click scraping in New Application wizard
  - Auto-fills company name and role from job posting
  - No manual copy-pasting needed
- **NEW: Target Company List**
  - Track companies you want to apply to
  - Filter by industry (SaaS, FinTech, etc.)
  - Set priority (High/Medium/Low)
  - Track status (Researching/Ready/Applied)
  - Add company details (website, careers page, LinkedIn)
  - Import companies from CSV
  - Link to applications when applied
- **Enhanced Application Workflow**
  - Fetch job description directly from URL
  - Auto-populate company and role fields
  - Streamlined application creation

### 2026-02-10 - Automation Release (v0.7.0)
- **NEW: Email Automation System**
  - Auto-scheduled email scanning (configurable interval)
  - Background thread for continuous monitoring
  - Auto-match emails to applications by company name
  - Auto-update application status from email content
  - Desktop notifications for important events
  - Manual scan trigger with instant results
  - Automation controls in Settings page
- **NEW: Desktop Notifications**
  - Interview invite notifications with date/time
  - Job offer alerts
  - Rejection notifications
  - Status change alerts
  - Email scan summary notifications
  - macOS, Linux, Windows support
- **Enhanced Email Intelligence**
  - Email classification (interview, offer, rejection, etc.)
  - Interview date/time extraction
  - Suggested status updates based on email type
  - High-confidence auto-updates only
  - Smart status progression logic

### 2026-02-10 - Email Scanner Release (v0.6.0)
- Added interactive email scanner tab
- Implemented email-to-application linking
- Added bulk email operations
- Created application timeline view
- Added email count metrics
- Fixed division by zero in analytics
- Consolidated to single app version
- Created single comprehensive README

### 2026-02-07 - UI Improvements
- Added clean professional design
- Removed emojis from UI
- Improved text readability
- Added light theme
- Fixed contrast issues

### 2026-02-05 - MCP Integration
- Created MCP server with 15 tools
- Added email tracking tools
- Integrated with Claude Code

### Earlier
- Initial application tracking
- Database schema
- Basic UI
- AI cover letter generation
- Email tracker foundation

---

## 📝 Notes

- Email features work but need intelligence layer (parsing, auto-updates, notifications)
- Focus on making email features smart before adding more features
- User feedback: wants email tracking integrated, not separate
- Priority: Email intelligence > Calendar > Everything else

---

## 🎯 Next Up

**Immediate focus**: Email content analysis with AI

**Why**: Email scanner is functional but not intelligent - it can see emails but can't understand them. Adding AI parsing will:
1. Auto-extract interview dates/times
2. Auto-classify email types
3. Auto-update application statuses
4. Enable smart notifications
5. Make the tool actually useful for daily use

**After that**: Calendar integration + reminders

---

**Version History**:
- v0.7.0 (Current) - Email Automation & Notifications
- v0.6.0 - Full Featured (Email Scanner Beta)
- v0.5.0 - Email Integration
- v0.4.0 - MCP Integration
- v0.3.0 - UI Redesign
- v0.2.0 - Basic Tracking
- v0.1.0 - Initial Release
