# Email Automation Guide

## What's Been Added (v0.7.0)

Your application tracker now has **full email automation**! Here's what works:

### 🚀 Automated Email Scanning

**Background monitoring** that runs continuously:
- Scans your Gmail inbox automatically on schedule
- Configurable interval: 15, 30, 60, or 120 minutes
- Runs in background thread (won't freeze the UI)
- Manual "Scan Now" button for instant results

### 🤖 Auto Status Updates

**Smart status management** based on email content:
- Interview invites → Status: "Interview"
- Job offers → Status: "Offer"
- Rejections → Status: "Rejected"
- High-confidence only (60%+ confidence required)
- Won't downgrade status (smart progression logic)
- All changes logged in application notes

### 🔔 Desktop Notifications

**Instant alerts** for important events:
- 🎉 Interview invitations (with extracted date/time)
- 🎉 Job offers
- 📧 Status changes
- ❌ Rejections
- Works on macOS, Linux, and Windows

### 🎯 Email Intelligence

**AI-powered email analysis**:
- Classifies email type (interview, offer, rejection, scheduling, etc.)
- Extracts interview dates and times
- Matches emails to applications by company name
- Suggests appropriate status updates
- Confidence scoring for each classification

## How to Use

### Quick Start

1. **Launch the app**:
   ```bash
   ./run_ui.sh
   ```

2. **Go to Settings** (⚙️ tab)

3. **Scroll to "Email Automation" section**

4. **Configure**:
   - ✅ Check "Auto-update application status"
   - 📅 Choose scan interval (default: 30 minutes)
   - 🔔 Enable notifications
   - 🚀 Click "Start Automation"

That's it! The system is now monitoring your inbox.

### Manual Scanning

Want to scan right now?
- Settings → Email Automation → "Scan Now"
- Results show immediately
- See matched emails and status updates

### View Results

**Check what automation found**:
1. Go to **Email Tracking** tab
2. See all classified emails
3. Check which are linked to applications
4. Review suggested status changes

**View application timeline**:
1. Go to **Applications** tab
2. Click on any application
3. Go to "History" tab
4. See all emails chronologically

## Safety Features

### Smart Auto-Updates

The system is **careful** about auto-updating:

✅ **Will update**:
- High-confidence classifications (60%+)
- Forward progression (Applied → Interview → Offer)
- Rejections (at any stage)
- Offers (if not already rejected/withdrawn)

❌ **Won't update**:
- Low-confidence classifications (<60%)
- Backwards progression (Interview → Applied)
- If already at suggested status
- Uncertain email types

### Full Control

You're always in control:
- **Stop anytime**: Click "Stop Automation" in Settings
- **Disable auto-updates**: Uncheck the box (keeps scanning, no auto-status)
- **Disable notifications**: Uncheck to silence alerts
- **Review changes**: All auto-updates logged in notes

## What It Does Automatically

### Every Scan Cycle

1. **Connect** to your Gmail via IMAP
2. **Search** for application-related emails (last 7 days)
3. **Classify** each email using AI or keywords:
   - interview_invite
   - offer
   - rejection
   - scheduling
   - confirmation
   - follow_up
   - other
4. **Extract** dates, times, and key details
5. **Match** emails to tracked applications by company name
6. **Update** application status (if confidence is high)
7. **Notify** you of important events
8. **Save** all analyses to database
9. **Disconnect** from Gmail

### Example Workflow

**Scenario**: You applied to "Example Corp" for Software Engineer role.

1. **You get email**: "Interview Invitation - Software Engineer"
2. **Automation runs**:
   - Scans inbox
   - Finds the email
   - Classifies as "interview_invite" (95% confidence)
   - Extracts date: "2026-02-15" and time: "14:00"
   - Matches to "Example Corp" application
   - Updates status: "Applied" → "Interview"
   - Adds note: "[Auto-updated from email: interview_invite]"
   - Sends notification: "🎉 Interview Invitation - Example Corp on 2026-02-15"
3. **You see**: Desktop notification + updated status in app

## Configuration Options

### Scan Interval

Choose how often to scan:
- **15 minutes**: Aggressive (good for active job search)
- **30 minutes**: Balanced (recommended)
- **60 minutes**: Moderate (reduces API calls)
- **120 minutes**: Conservative (minimal monitoring)

### Auto-Update Status

**Enabled** (recommended):
- Automatically changes application status based on emails
- Saves you manual work
- All changes logged and reviewable

**Disabled**:
- Scans and classifies emails
- Suggests status updates
- You manually review and apply

### Notifications

**Enabled** (recommended):
- Get instant alerts for important events
- Never miss an interview invite
- Stay on top of your job search

**Disabled**:
- Silent mode
- Check app manually for updates

## Technical Details

### Email Classification

**AI-powered** (if Groq/Google/OpenAI configured):
- Uses LLM to classify emails
- Extracts dates, times, locations
- Provides detailed summaries
- High accuracy

**Keyword-based** (fallback):
- Fast, local, no API needed
- Good accuracy for common patterns
- No external dependencies

### Email Matching

**How it matches emails to applications**:
1. Extract company name from email sender/subject
2. Compare to tracked applications
3. Match if company name appears in:
   - Email sender address
   - Email subject line
   - For multi-word companies: at least 2 words match

### Status Progression

**Valid progressions**:
- Draft → Applied
- Applied → Phone Screen → Interview → Final Round → Offer → Accepted
- Any status → Rejected

**Invalid progressions** (won't auto-update):
- Interview → Applied
- Offer → Interview
- Accepted → Anything

## Troubleshooting

### Automation not starting

**Check**:
1. Gmail configured in Settings? (Email + App Password in .env)
2. Click "Start Automation" button?
3. Check terminal for error messages

### No emails found

**Possible reasons**:
1. No application emails in last 7 days
2. Gmail connection issue
3. Search keywords too restrictive

**Solutions**:
- Click "Scan Now" for immediate test
- Check Gmail credentials
- Verify IMAP is enabled in Gmail

### Status not updating

**Possible reasons**:
1. Auto-update disabled
2. Low confidence classification (<60%)
3. Invalid status progression
4. Already at suggested status

**Solutions**:
- Enable "Auto-update application status"
- Check email classification confidence
- Manually review in Email Tracking tab

### Notifications not working

**macOS**: Should work out of the box
**Linux**: Install `notify-send` (`sudo apt-get install libnotify-bin`)
**Windows**: Install `win10toast` (`pip install win10toast`)

## Privacy & Security

### Your Data Stays Local

✅ **All data stored locally**:
- SQLite database on your machine
- No cloud uploads
- No external data sharing

✅ **Gmail access**:
- Read-only IMAP connection
- Only accesses emails (doesn't send or delete)
- Uses App Password (not your main password)

✅ **AI calls**:
- Only when analyzing emails
- Email content sent to provider for classification
- Choose your provider (Groq, Google, OpenAI, or local)

## Statistics

**Track automation performance**:
- Total scans run
- Emails processed
- Statuses auto-updated
- Last scan time

**View in Settings → Email Automation section**

## Next Steps

Now that automation is working, next priorities:

1. **Calendar integration** - Auto-create Google Calendar events from interview emails
2. **Email replies** - Respond to emails directly from the app
3. **Follow-up reminders** - Automated reminders after 7, 14, 30 days

See `CHANGELOG.md` for full roadmap.

---

**Summary**: Your app now monitors your inbox 24/7, automatically updates application statuses, and sends you instant notifications. Just click "Start Automation" in Settings and let it run!
