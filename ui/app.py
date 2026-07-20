"""
Streamlit UI for AI Application Agent
Enhanced with better styling, pagination, and email analysis.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, date, time
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agent import ApplicationAgent
from tools.data_tools import (
    add_application,
    get_applications,
    get_application_stats,
    get_application_by_id,
    get_application_history,
    save_full_application,
    update_application,
    add_history_event,
    load_cv_path
)
from tools.job_analyzer import batch_analyze_all, analyze_job, get_roles_by_category, categorize_role
from tools.email_tracker import GmailTracker, check_gmail_setup
from tools.email_automation import get_automation
from tools.job_scraper import JobScraper
from db.session import SessionLocal, init_db
from db.models import Application
from db.target_companies import (
    get_target_companies, add_target_company, update_target_company,
    delete_target_company, mark_as_applied
)

# Import new utilities
from ui.utils.formatters import (
    STATUS_ICONS, EVENT_ICONS, ROLE_ICONS, SENIORITY_ICONS,
    get_score_color as get_score_emoji, format_date, format_date_short, format_datetime,
    truncate, format_role_category, format_status_with_icon
)
from ui.utils.state import (
    get_provider, set_provider, get_provider_index, PROVIDERS,
    init_session_state, reset_workflow, get_page, set_page, next_page, prev_page
)
from ui.utils.styles import (
    inject_custom_styles, render_status_badge, render_score_indicator,
    render_confidence_bar, render_action_item
)
from ui.config import (
    COLORS, STATUS_OPTIONS, STATUS_COLORS, ITEMS_PER_PAGE,
    EMAIL_TYPE_CONFIG, get_score_color, get_status_color,
    SPACING, BORDER_RADIUS
)
from ui.components.tables import render_compact_table, render_application_table
from ui.components.dialogs import confirm_delete, confirm_bulk_delete

# Page config - Force light theme
st.set_page_config(
    page_title="AI Application Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure tables exist (fresh clones previously crashed with "no such table")
init_db()

# Initialize session state
init_session_state()

# Inject custom styles
inject_custom_styles()


def days_since(dt) -> str:
    """Return a short human-readable string like '3d ago' or 'today'."""
    if dt is None:
        return ""
    delta = (datetime.now() - dt).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "1d ago"
    return f"{delta}d ago"


def init_agent(provider: str = "auto"):
    """Initialize or get the agent, reinitializing if provider changed."""
    current = st.session_state.agent
    if current is None or getattr(current, 'active_provider', None) != provider:
        st.session_state.agent = ApplicationAgent(provider=provider)
    return st.session_state.agent


def main():
    # Sidebar navigation
    st.sidebar.title("🤖 AI Application Agent")

    page = st.sidebar.radio(
        "Navigate",
        ["📊 Dashboard", "📋 Applications", "📧 Email", "📝 CV & Insights", "⚙️ Settings"]
    )

    # Provider selector in sidebar - now persists
    st.sidebar.markdown("---")
    st.sidebar.subheader("AI Provider")
    provider_idx = get_provider_index()
    provider = st.sidebar.selectbox(
        "Select Provider",
        PROVIDERS,
        index=provider_idx,
        help="Groq and Google are FREE!",
        key="provider_selector"
    )

    # Update provider if changed
    if provider != get_provider():
        set_provider(provider)

    # Route to pages
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📋 Applications":
        show_applications_page()
    elif page == "📧 Email":
        show_email_tracking()
    elif page == "📝 CV & Insights":
        show_cv_insights(get_provider())
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Dashboard — clean overview for daily job search screening."""
    st.title("📊 Dashboard")

    stats = get_application_stats()
    all_apps = get_applications(limit=1000)

    # ── Top stats row ────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", stats['total'])
    c2.metric("Applied", stats['applied'])
    c3.metric("Interviews", stats['interview'])
    c4.metric("Offers", stats['offer'])
    c5.metric("Rejected", stats['rejected'])

    st.markdown("---")

    # ── Pipeline funnel + rates ──────────────────────────────────────────────
    if stats['total'] > 0:
        interview_rate = round(stats['interview'] / stats['total'] * 100, 1)
        offer_rate = round(stats['offer'] / stats['total'] * 100, 1)
        active = stats['total'] - stats['rejected'] - stats['offer'] - stats.get('accepted', 0)

        left, right = st.columns([3, 1])

        with left:
            st.markdown("**Pipeline**")
            from collections import Counter
            status_counts = Counter(a.status for a in all_apps)
            pipeline_stages = [
                ("Applied", "🟡"),
                ("Phone Screen", "📞"),
                ("Technical Interview", "💻"),
                ("Interview", "🟢"),
                ("Final Round", "🎯"),
                ("Offer", "🎉"),
            ]
            parts = []
            for stage, icon in pipeline_stages:
                n = status_counts.get(stage, 0)
                if n > 0:
                    parts.append(f"{icon} {stage} **{n}**")
            if parts:
                st.markdown(" → ".join(parts))
            else:
                st.caption("No active pipeline yet")

        with right:
            st.metric("Interview rate", f"{interview_rate}%")
            st.metric("Active", active)

    st.markdown("---")

    # ── Recent applications ──────────────────────────────────────────────────
    st.markdown("**Recent Applications**")

    recent = get_applications(limit=15)
    if recent:
        header = st.columns([3, 4, 2, 1, 1])
        header[0].caption("Company")
        header[1].caption("Role")
        header[2].caption("Status")
        header[3].caption("Score")
        header[4].caption("Age")

        for app in recent:
            row = st.columns([3, 4, 2, 1, 1])
            row[0].write(f"**{app.company}**")
            row[1].write(truncate(app.role or "—", 45))
            status_icon = STATUS_ICONS.get(app.status, "⚪")
            row[2].write(f"{status_icon} {app.status}")
            row[3].write(f"{app.fit_score:.0f}" if app.fit_score else "—")
            row[4].write(days_since(app.application_date))
    else:
        st.info("No applications yet — go to Applications → + New Application to add one.")


def _render_application_details(app):
    """Render the detailed tabs view for a single application."""
    tabs = st.tabs(["📋 Overview", "📝 Cover Letter", "📜 History", "🎯 Interview Prep"])

    # TAB 1: Overview & Edit
    with tabs[0]:
        col1, col2 = st.columns(2)

        with col1:
            # Status update with icons
            current_idx = STATUS_OPTIONS.index(app.status) if app.status in STATUS_OPTIONS else 0
            new_status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=current_idx,
                format_func=lambda x: f"{STATUS_ICONS.get(x, '⚪')} {x}",
                key=f"status_{app.id}"
            )

            # Notes
            new_notes = st.text_area("Notes", app.notes or "", height=80, key=f"notes_{app.id}")

            # Fit analysis summary
            if app.fit_score:
                st.write(f"**Fit Score:** {app.fit_score}/10")
            if app.role_category:
                st.write(f"**Role Type:** {format_role_category(app.role_category)}")
            if app.seniority_level:
                st.write(f"**Seniority:** {app.seniority_level.title() if app.seniority_level else 'N/A'}")

        with col2:
            if app.job_url:
                st.write(f"🔗 [Open Job Posting]({app.job_url})")
            st.write(f"📅 Applied: {format_date(app.application_date)}")
            if app.created_at:
                st.write(f"📁 Created: {format_date(app.created_at)}")

            # Fit analysis details
            if app.fit_analysis_json:
                try:
                    fit_data = json.loads(app.fit_analysis_json)
                    if fit_data.get('strengths'):
                        st.write("**Strengths:**", ", ".join(str(s) for s in fit_data['strengths'][:4]))
                    if fit_data.get('gaps'):
                        st.write("**Gaps:**", ", ".join(str(g) for g in fit_data['gaps'][:4]))
                except:
                    pass

        # Job description
        if app.job_description:
            with st.expander("View Job Description"):
                st.text_area("JD", app.job_description, height=150, key=f"jd_{app.id}", disabled=True)

        # Interview Scheduling & Calendar Integration
        if app.status in ["Phone Screen", "Interview", "Technical Interview", "Final Round"]:
            st.markdown("---")
            st.subheader("📅 Interview Details")

            # Check if we have extracted interview info from emails
            from db.models import EmailAnalysis
            db = SessionLocal()
            email_analysis = db.query(EmailAnalysis).filter(
                EmailAnalysis.application_id == app.id,
                EmailAnalysis.email_type.in_(["interview_invite", "scheduling"])
            ).order_by(EmailAnalysis.received_date.desc()).first()

            interview_date = None
            interview_time = None
            interviewer = None
            location = ""

            if email_analysis and email_analysis.extracted_date and email_analysis.extracted_time:
                interview_date = email_analysis.extracted_date
                interview_time = email_analysis.extracted_time

                # Try to extract additional details
                if email_analysis.key_details:
                    try:
                        import json as json_lib
                        details = json_lib.loads(email_analysis.key_details)
                        interviewer = details.get('interviewer_name', '')
                        location = details.get('location', '') or details.get('format', '')
                    except:
                        pass

                st.success(f"✅ Interview scheduled: {interview_date} at {interview_time}")
                if interviewer:
                    st.write(f"👤 Interviewer: {interviewer}")
                if location:
                    st.write(f"📍 Location: {location}")

            db.close()

            # Manual date/time input
            col1, col2, col3 = st.columns(3)
            with col1:
                try:
                    _date_val = datetime.strptime(interview_date, "%Y-%m-%d").date() if interview_date else None
                except ValueError:
                    _date_val = None
                manual_date = st.date_input(
                    "Interview Date",
                    value=_date_val,
                    key=f"int_date_{app.id}"
                )
            with col2:
                try:
                    _time_val = datetime.strptime(interview_time, "%H:%M").time() if interview_time else None
                except ValueError:
                    _time_val = None
                manual_time = st.time_input(
                    "Interview Time",
                    value=_time_val,
                    key=f"int_time_{app.id}"
                )
            with col3:
                duration = st.selectbox(
                    "Duration",
                    options=[30, 45, 60, 90, 120],
                    index=2,  # Default 60 minutes
                    format_func=lambda x: f"{x} minutes",
                    key=f"int_duration_{app.id}"
                )

            manual_location = st.text_input(
                "Location / Video Link",
                value=location,
                placeholder="Office address or Zoom/Teams link",
                key=f"int_location_{app.id}"
            )

            # Add to Calendar button
            if manual_date and manual_time:
                if st.button("📅 Add to Calendar", key=f"cal_{app.id}", type="primary"):
                    from utils.calendar_utils import create_interview_ics
                    try:
                        # Format date and time
                        date_str = manual_date.strftime("%Y-%m-%d")
                        time_str = manual_time.strftime("%H:%M")

                        # Generate .ics file
                        ics_content = create_interview_ics(
                            company=app.company,
                            role=app.role or "Position",
                            interview_date=date_str,
                            interview_time=time_str,
                            duration_minutes=duration,
                            location=manual_location,
                            notes=app.notes or "",
                            interviewer=interviewer or ""
                        )

                        # Create download button
                        filename = f"{app.company.replace(' ', '_')}_interview.ics"
                        st.download_button(
                            label="⬇️ Download Calendar File (.ics)",
                            data=ics_content,
                            file_name=filename,
                            mime="text/calendar",
                            key=f"download_ics_{app.id}",
                            help="Download and open with your calendar app (Google Calendar, Outlook, Apple Calendar)"
                        )
                        st.success("✅ Calendar file ready! Click above to download.")
                        st.info("💡 **Tip:** After downloading, open the .ics file. It will automatically add to your default calendar with reminders 1 day and 1 hour before.")
                    except Exception as e:
                        st.error(f"❌ Error generating calendar file: {e}")

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("💾 Save", key=f"save_{app.id}", type="primary"):
                update_application(
                    application_id=app.id,
                    status=new_status,
                    notes=new_notes
                )
                st.success("✅ Saved!")
                st.rerun()
        with col2:
            if st.button("🗑️ Delete", key=f"delete_btn_{app.id}"):
                st.session_state[f'confirm_delete_{app.id}'] = True

            # Show confirmation if delete was clicked
            if st.session_state.get(f'confirm_delete_{app.id}', False):
                if confirm_delete(f"{app.company} - {app.role}", key=f"delete_{app.id}"):
                    db = SessionLocal()
                    db_app = db.query(Application).filter(Application.id == app.id).first()
                    if db_app:
                        db.delete(db_app)
                        db.commit()
                    db.close()
                    # Clear confirmation state
                    st.session_state[f'confirm_delete_{app.id}'] = False
                    st.success(f"✅ Deleted {app.company}")
                    st.rerun()

    # TAB 2: Cover Letter
    with tabs[1]:
        if app.cover_letter_text:
            st.text_area("Saved Cover Letter", app.cover_letter_text, height=300, key=f"cl_{app.id}", disabled=True)

            if st.button("📋 Copy to Clipboard", key=f"copy_cl_{app.id}"):
                st.code(app.cover_letter_text)
                st.info("Select and copy the text above")
        else:
            st.info("No cover letter saved for this application.")
            st.caption("Generate one using the 'New Application' workflow.")

    # TAB 3: History
    with tabs[2]:
        history = get_application_history(app.id)
        if history:
            for event in history[:10]:
                event_icon = EVENT_ICONS.get(event.event_type, "📋")

                event_text = f"{event_icon} **{event.event_type.replace('_', ' ').title()}**"
                if event.old_value and event.new_value:
                    event_text += f": {event.old_value} → {event.new_value}"
                elif event.new_value:
                    event_text += f": {event.new_value}"

                st.write(f"{event_text}")
                st.caption(f"{format_datetime(event.created_at)} {event.details or ''}")
        else:
            st.info("No history recorded yet.")

    # TAB 4: Interview Prep
    with tabs[3]:
        from db.interview_prep import (
            get_or_create_interview_prep, update_interview_prep,
            add_practice_question, get_practice_questions,
            update_practice_question, get_common_questions,
            add_interview_feedback, get_interview_feedback
        )

        # Only show if in interview stages
        if app.status not in ["Phone Screen", "Interview", "Technical Interview", "Final Round", "Offer"]:
            st.info("📋 Interview prep will be available when status is set to interview stage")
        else:
            # Get or create interview prep
            prep = get_or_create_interview_prep(app.id)

            # Sub-tabs for different prep areas
            prep_tabs = st.tabs(["📚 Research", "❓ Practice Questions", "📝 Post-Interview"])

            # PREP TAB 1: Company Research
            with prep_tabs[0]:
                st.markdown("### 📚 Company Research")
                st.caption("Prepare your knowledge about the company")

                company_research = st.text_area(
                    "Company Overview & Products",
                    value=prep.company_research or "",
                    height=100,
                    placeholder="What does the company do? Main products/services? Key customers?",
                    key=f"research_{app.id}"
                )

                company_culture = st.text_area(
                    "Company Culture & Values",
                    value=prep.company_culture or "",
                    height=100,
                    placeholder="What are their core values? What's the culture like?",
                    key=f"culture_{app.id}"
                )

                recent_news = st.text_area(
                    "Recent News & Developments",
                    value=prep.recent_news or "",
                    height=100,
                    placeholder="Recent funding, product launches, news mentions?",
                    key=f"news_{app.id}"
                )

                st.markdown("### 🎯 Your Preparation")

                key_skills = st.text_area(
                    "Key Skills to Highlight",
                    value=prep.key_skills or "",
                    height=80,
                    placeholder="Which of your skills match this role best?",
                    key=f"skills_{app.id}"
                )

                relevant_experience = st.text_area(
                    "Relevant Experience to Emphasize",
                    value=prep.relevant_experience or "",
                    height=80,
                    placeholder="Which projects/experiences should you mention?",
                    key=f"experience_{app.id}"
                )

                if st.button("💾 Save Research Notes", key=f"save_research_{app.id}", type="primary"):
                    update_interview_prep(
                        application_id=app.id,
                        company_research=company_research,
                        company_culture=company_culture,
                        recent_news=recent_news,
                        key_skills=key_skills,
                        relevant_experience=relevant_experience
                    )
                    st.success("✅ Research notes saved!")
                    st.rerun()

            # PREP TAB 2: Practice Questions
            with prep_tabs[1]:
                st.markdown("### ❓ Practice Questions")

                # Show common questions by category
                question_category = st.selectbox(
                    "Question Category",
                    ["behavioral", "technical", "sales_engineer", "solution_architect", "questions_to_ask"],
                    format_func=lambda x: x.replace("_", " ").title(),
                    key=f"q_cat_{app.id}"
                )

                common_qs = get_common_questions(question_category)
                if common_qs:
                    st.markdown(f"#### Common {question_category.replace('_', ' ').title()} Questions:")
                    for i, q in enumerate(common_qs, 1):
                        st.write(f"{i}. {q}")

                st.markdown("---")

                # Add custom question
                with st.expander("➕ Add Custom Practice Question"):
                    new_question = st.text_area("Question", key=f"new_q_{app.id}")
                    q_type = st.selectbox(
                        "Type",
                        ["behavioral", "technical", "situational", "company-specific"],
                        key=f"new_q_type_{app.id}"
                    )
                    if st.button("Add Question", key=f"add_q_{app.id}"):
                        if new_question:
                            add_practice_question(
                                interview_prep_id=prep.id,
                                question=new_question,
                                question_type=q_type
                            )
                            st.success("✅ Question added!")
                            st.rerun()

                # Show saved practice questions
                st.markdown("### 📝 Your Practice Questions")
                saved_questions = get_practice_questions(prep.id)

                if saved_questions:
                    for q in saved_questions:
                        with st.expander(f"{'🟢' if q.confidence_level and q.confidence_level >= 4 else '🟡' if q.confidence_level else '🔴'} {q.question[:80]}..."):
                            st.write(f"**Type:** {q.question_type.title()}")
                            st.write(f"**Practiced:** {q.times_practiced} times")

                            answer = st.text_area(
                                "Your Prepared Answer",
                                value=q.prepared_answer or "",
                                height=150,
                                key=f"answer_{q.id}"
                            )

                            confidence = st.slider(
                                "Confidence Level",
                                1, 5, q.confidence_level or 3,
                                help="How confident are you with this answer?",
                                key=f"conf_{q.id}"
                            )

                            if st.button("💾 Save Answer", key=f"save_answer_{q.id}"):
                                update_practice_question(
                                    question_id=q.id,
                                    prepared_answer=answer,
                                    confidence_level=confidence
                                )
                                st.success("✅ Answer saved!")
                                st.rerun()
                else:
                    st.info("No practice questions yet. Add some above!")

                # Practice timer
                st.markdown("---")
                st.markdown("### ⏱️ Practice Timer")
                st.caption("Practice answering questions with a timer")

                timer_minutes = st.number_input(
                    "Minutes per question",
                    min_value=1,
                    max_value=10,
                    value=2,
                    key=f"timer_{app.id}"
                )

                if st.button("▶️ Start Practice Session", key=f"start_timer_{app.id}"):
                    st.info(f"⏱️ {timer_minutes} minute timer! Practice your answers out loud.")
                    import time
                    progress_bar = st.progress(0)
                    for i in range(timer_minutes * 60):
                        time.sleep(1)
                        progress_bar.progress((i + 1) / (timer_minutes * 60))
                    st.success("✅ Time's up! How did you do?")

            # PREP TAB 3: Post-Interview Feedback
            with prep_tabs[2]:
                st.markdown("### 📝 Post-Interview Reflection")
                st.caption("Record feedback after completing an interview")

                # Form for adding new feedback
                with st.form(f"feedback_form_{app.id}"):
                    st.subheader("Add Interview Feedback")

                    col1, col2 = st.columns(2)
                    with col1:
                        interview_date = st.date_input("Interview Date", key=f"fb_date_{app.id}")
                        interview_type = st.selectbox(
                            "Interview Type",
                            ["phone_screen", "technical", "behavioral", "hiring_manager", "final_round"],
                            format_func=lambda x: x.replace("_", " ").title(),
                            key=f"fb_type_{app.id}"
                        )
                    with col2:
                        interviewer = st.text_input("Interviewer Name", key=f"fb_int_{app.id}")
                        duration = st.number_input("Duration (minutes)", 30, 180, 60, key=f"fb_dur_{app.id}")

                    went_well = st.text_area("What went well?", height=100, key=f"fb_well_{app.id}")
                    went_poorly = st.text_area("What could improve?", height=100, key=f"fb_poor_{app.id}")
                    questions_asked = st.text_area("Questions they asked", height=100, key=f"fb_qs_{app.id}")

                    col1, col2 = st.columns(2)
                    with col1:
                        overall_rating = st.slider("Overall Rating", 1, 5, 3, key=f"fb_rating_{app.id}")
                    with col2:
                        confidence = st.slider("Confidence After", 1, 5, 3, key=f"fb_conf_{app.id}")

                    next_steps = st.text_area("Next Steps", key=f"fb_next_{app.id}")

                    if st.form_submit_button("💾 Save Feedback", type="primary"):
                        add_interview_feedback(
                            application_id=app.id,
                            interview_date=datetime.combine(interview_date, datetime.min.time()),
                            interview_type=interview_type,
                            interviewer=interviewer,
                            duration_minutes=duration,
                            went_well=went_well,
                            went_poorly=went_poorly,
                            questions_asked=questions_asked,
                            overall_rating=overall_rating,
                            confidence_after=confidence,
                            next_steps=next_steps
                        )
                        st.success("✅ Feedback saved!")
                        st.rerun()

                # Show previous feedback
                st.markdown("---")
                st.markdown("### 📚 Previous Interview Feedback")
                feedback_list = get_interview_feedback(app.id)

                if feedback_list:
                    for fb in feedback_list:
                        with st.expander(f"{'⭐' * fb.overall_rating} {fb.interview_type.replace('_', ' ').title()} - {fb.interview_date.strftime('%Y-%m-%d')}"):
                            if fb.interviewer:
                                st.write(f"**Interviewer:** {fb.interviewer}")
                            st.write(f"**Duration:** {fb.duration_minutes} minutes")
                            st.write(f"**Rating:** {'⭐' * fb.overall_rating} ({fb.overall_rating}/5)")
                            st.write(f"**Confidence:** {fb.confidence_after}/5")

                            if fb.went_well:
                                st.markdown("**✅ Went Well:**")
                                st.write(fb.went_well)

                            if fb.went_poorly:
                                st.markdown("**⚠️ Could Improve:**")
                                st.write(fb.went_poorly)

                            if fb.questions_asked:
                                st.markdown("**❓ Questions Asked:**")
                                st.write(fb.questions_asked)

                            if fb.next_steps:
                                st.markdown("**🎯 Next Steps:**")
                                st.write(fb.next_steps)
                else:
                    st.info("No interview feedback yet. Complete an interview and add your reflections!")


def show_job_search_tab():
    """Job board search links + URL import (extracted from workflow.py)."""
    from tools.job_search import JobBoardSearch, get_popular_job_boards

    st.markdown("### 🔍 Search Job Boards")

    col1, col2 = st.columns(2)
    with col1:
        role = st.text_input(
            "Role",
            value="Solutions Engineer",
            placeholder="e.g., Sales Engineer, Solution Architect"
        )
    with col2:
        location = st.selectbox(
            "Location",
            ["Europe", "Remote", "Germany", "UK", "Ireland", "France", "Netherlands"]
        )

    col1, col2 = st.columns(2)
    with col1:
        remote = st.checkbox("Include Remote Jobs", value=True)
    with col2:
        saas_only = st.checkbox("SaaS Companies Only", value=True)

    if st.button("🔍 Generate Job Board Links", type="primary", use_container_width=True):
        searcher = JobBoardSearch()
        keywords = ["SaaS", "B2B"] if saas_only else None

        search_urls = searcher.build_search_urls(
            role=role,
            location=location,
            remote=remote,
            keywords=keywords
        )

        st.success(f"✅ Generated search links for {len(search_urls)} job boards")

        st.markdown("### 🔗 Job Board Search Links")
        st.caption("Click to open in new tab")

        for board, url in search_urls.items():
            st.markdown(f"""
            <div style='padding: 1rem; background: white; border-left: 4px solid #4F46E5;
                        border-radius: 5px; margin-bottom: 0.5rem;'>
                <a href='{url}' target='_blank' style='text-decoration: none; color: #2c3e50;'>
                    <strong>{board}</strong> →
                </a>
                <br>
                <small style='color: #7f8c8d;'>{url[:80]}...</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📌 Popular Job Boards")
    st.caption("Quick access to top job boards")

    job_boards = get_popular_job_boards()

    cols = st.columns(2)
    for idx, board in enumerate(job_boards):
        with cols[idx % 2]:
            st.markdown(f"""
            <div style='padding: 1rem; background: #f8f9fa; border-radius: 5px; margin-bottom: 0.5rem;'>
                <strong><a href='{board["url"]}' target='_blank'>{board["name"]}</a></strong>
                <br>
                <small>{board["description"]}</small>
                <br>
                <small style='color: #4F46E5;'>Best for: {board["best_for"]}</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🌐 Import Job from URL")
    st.caption("Paste a job posting URL to extract details")

    job_url = st.text_input(
        "Job URL",
        placeholder="https://linkedin.com/jobs/view/...",
        label_visibility="collapsed"
    )

    if st.button("📥 Import Job Details", use_container_width=True):
        if job_url:
            with st.spinner("Scraping job details..."):
                scraper = JobScraper()
                result = scraper.scrape_job(job_url)

                if result.get('success', True) and result.get('job_description'):
                    st.success("✅ Job details extracted!")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Company:** {result.get('company', 'Unknown')}")
                    with col2:
                        st.write(f"**Role:** {result.get('role', 'Unknown')}")

                    with st.expander("📄 View Job Description"):
                        st.text_area(
                            "Description",
                            result['job_description'],
                            height=200,
                            label_visibility="collapsed"
                        )

                    if st.button("➕ Add to Applications", type="primary"):
                        st.session_state.new_job_data = result
                        st.success("✅ Job data saved! Click '+ New Application' to continue.")
                else:
                    st.error(f"❌ Failed to extract job details: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a job URL")


def show_applications_page():
    """Applications page: list + target companies tab + find jobs tab; wizard on demand."""
    # If wizard is active, render it full-page
    if st.session_state.get('app_view') == 'new_application':
        if st.button("← Back to Applications"):
            st.session_state.app_view = 'list'
            reset_workflow()
            st.rerun()
        show_new_application(get_provider())
        return

    # Normal list view with header + New Application button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📋 Applications")
    with col2:
        if st.button("＋ New Application", type="primary"):
            st.session_state.app_view = 'new_application'
            reset_workflow()
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 My Applications", "🎯 Target Companies", "🔍 Find Jobs"])
    with tab1:
        show_applications()
    with tab2:
        show_target_companies()
    with tab3:
        show_job_search_tab()


def show_applications():
    """List all applications with pagination and improved layout."""
    st.title("📋 All Applications")

    # Initialize selected items in session state
    if 'selected_apps' not in st.session_state:
        st.session_state.selected_apps = set()

    # View mode selector
    view_mode = st.radio(
        "View Mode",
        ["📊 Table View", "📋 Detailed Cards", "🎯 Kanban Board"],
        horizontal=True,
        help="Choose how to display your applications"
    )

    st.markdown("---")

    # Quick Filter Presets - Improved with consistent sizing
    st.markdown("### ⚡ Quick Filters")

    # Create filter state if not exists
    if 'active_filter' not in st.session_state:
        st.session_state.active_filter = None

    filter_cols = st.columns(5)

    quick_filter = None

    filters = [
        ("🎯 Active", "active", "Not rejected or accepted"),
        ("⏳ Awaiting", "awaiting", "Applied > 7 days ago"),
        ("⭐ High Fit", "high_priority", "Fit score ≥ 8"),
        ("📅 This Week", "this_week", "Last 7 days"),
        ("📧 Follow-up", "follow_up", "Applied > 14 days")
    ]

    for idx, (label, filter_id, help_text) in enumerate(filters):
        with filter_cols[idx]:
            button_type = "primary" if st.session_state.active_filter == filter_id else "secondary"
            if st.button(label, help=help_text, use_container_width=True, key=f"filter_{filter_id}",
                        type=button_type):
                if st.session_state.active_filter == filter_id:
                    st.session_state.active_filter = None
                    quick_filter = None
                else:
                    st.session_state.active_filter = filter_id
                    quick_filter = filter_id

    # Use stored filter if button wasn't clicked
    if quick_filter is None and st.session_state.active_filter:
        quick_filter = st.session_state.active_filter

    # Bulk Actions - Cleaner layout
    if len(st.session_state.selected_apps) > 0:
        st.markdown("---")
        st.markdown(f"### 🎯 Bulk Actions • **{len(st.session_state.selected_apps)} selected**")

        bulk_col1, bulk_col2, bulk_col3 = st.columns([2, 2, 2])

        with bulk_col1:
            if st.button("✅ Select All", use_container_width=True, key="select_all_btn"):
                st.session_state.select_all_pending = True

        with bulk_col2:
            new_bulk_status = st.selectbox(
                "Change status to:",
                STATUS_OPTIONS,
                key="bulk_status_select"
            )
            if st.button("💾 Update Status", use_container_width=True, key="bulk_update"):
                for app_id in st.session_state.selected_apps:
                    update_application(app_id, status=new_bulk_status)
                st.success(f"✅ Updated {len(st.session_state.selected_apps)} applications")
                st.session_state.selected_apps = set()
                st.rerun()

        with bulk_col3:
            if st.button("🗑️ Delete Selected", use_container_width=True, key="bulk_delete_btn"):
                st.session_state.confirm_bulk_delete = True

        # Bulk delete confirmation
        if st.session_state.get('confirm_bulk_delete', False):
            if confirm_bulk_delete(len(st.session_state.selected_apps), key="bulk_delete_confirm"):
                db = SessionLocal()
                for app_id in st.session_state.selected_apps:
                    db_app = db.query(Application).filter(Application.id == app_id).first()
                    if db_app:
                        db.delete(db_app)
                db.commit()
                db.close()
                count = len(st.session_state.selected_apps)
                st.session_state.selected_apps = set()
                st.session_state.confirm_bulk_delete = False
                st.success(f"✅ Deleted {count} applications")
                st.rerun()

    st.markdown("---")

    # Filters - Clean layout
    st.markdown("---")
    st.markdown("### 🔍 Search & Filter")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            "Search",
            placeholder="🔍 Search company, role, description, notes, or cover letter...",
            label_visibility="collapsed"
        )
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All"] + STATUS_OPTIONS,
            label_visibility="collapsed"
        )

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (newest)", "Date (oldest)", "Fit Score", "Company"],
            label_visibility="collapsed"
        )
    with col2:
        items_per_page = st.selectbox(
            "Per page",
            [10, 20, 50, 100],
            index=1,
            label_visibility="collapsed"
        )
    with col3:
        # Clear filters button
        if st.button("🔄 Clear Filters", use_container_width=True):
            st.session_state.active_filter = None
            st.rerun()

    # Get applications
    status = None if status_filter == "All" else status_filter
    applications = get_applications(status=status, limit=500)

    # Apply quick filter
    if quick_filter:
        from datetime import datetime, timedelta
        now = datetime.now()

        if quick_filter == "active":
            # Not rejected or accepted
            applications = [a for a in applications if a.status not in ["Rejected", "Accepted", "Withdrawn"]]
        elif quick_filter == "awaiting":
            # Applied status for > 7 days
            seven_days_ago = now - timedelta(days=7)
            applications = [a for a in applications
                          if a.status == "Applied" and a.application_date
                          and a.application_date < seven_days_ago]
        elif quick_filter == "high_priority":
            # Score >= 8
            applications = [a for a in applications if a.fit_score and a.fit_score >= 8]
        elif quick_filter == "this_week":
            # Last 7 days
            seven_days_ago = now - timedelta(days=7)
            applications = [a for a in applications
                          if a.application_date and a.application_date >= seven_days_ago]
        elif quick_filter == "follow_up":
            # Applied > 14 days ago, not responded
            fourteen_days_ago = now - timedelta(days=14)
            applications = [a for a in applications
                          if a.status == "Applied" and a.application_date
                          and a.application_date < fourteen_days_ago]

    # Enhanced search - searches across all fields
    if search:
        search_lower = search.lower()
        filtered_apps = []
        for a in applications:
            # Search in company and role
            if search_lower in a.company.lower() or search_lower in (a.role or '').lower():
                filtered_apps.append(a)
                continue
            # Search in job description
            if a.job_description and search_lower in a.job_description.lower():
                filtered_apps.append(a)
                continue
            # Search in notes
            if a.notes and search_lower in a.notes.lower():
                filtered_apps.append(a)
                continue
            # Search in cover letter
            if a.cover_letter_text and search_lower in a.cover_letter_text.lower():
                filtered_apps.append(a)
                continue
        applications = filtered_apps

    # Sort
    if sort_by == "Date (oldest)":
        applications = sorted(applications, key=lambda x: x.application_date or datetime.min)
    elif sort_by == "Fit Score":
        applications = sorted(applications, key=lambda x: x.fit_score or 0, reverse=True)
    elif sort_by == "Company":
        applications = sorted(applications, key=lambda x: x.company.lower())

    # Pagination
    total_apps = len(applications)
    total_pages = max(1, (total_apps + items_per_page - 1) // items_per_page)
    current_page = min(get_page(), total_pages - 1)

    # Paginate
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_apps)
    paginated_apps = applications[start_idx:end_idx]

    # Handle "Select All Visible"
    if st.session_state.get('select_all_pending', False):
        for app in paginated_apps:
            st.session_state.selected_apps.add(app.id)
        st.session_state.select_all_pending = False
        st.rerun()

    # Results count and pagination
    st.markdown("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{total_apps} applications** • Showing {start_idx + 1}-{end_idx}")
    with col2:
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("◀", disabled=current_page == 0, use_container_width=True,
                        key="prev_page"):
                prev_page()
                st.rerun()
        with pcol2:
            st.markdown(f"<p style='text-align: center; margin-top: 0.5rem;'>Page {current_page + 1}/{total_pages}</p>",
                       unsafe_allow_html=True)
        with pcol3:
            if st.button("▶", disabled=current_page >= total_pages - 1, use_container_width=True,
                        key="next_page"):
                next_page()
                st.rerun()

    # Selection checkboxes - Cleaner layout
    if len(paginated_apps) > 0:
        with st.expander("✓ Select Applications", expanded=False):
            select_cols = st.columns(min(len(paginated_apps), 5))
            for idx, app in enumerate(paginated_apps):
                with select_cols[idx % 5]:
                    is_selected = st.checkbox(
                        f"{app.company[:15]}",
                        value=app.id in st.session_state.selected_apps,
                        key=f"select_{app.id}"
                    )
                    if is_selected and app.id not in st.session_state.selected_apps:
                        st.session_state.selected_apps.add(app.id)
                    elif not is_selected and app.id in st.session_state.selected_apps:
                        st.session_state.selected_apps.remove(app.id)

    st.markdown("---")

    # =========================================================================
    # TABLE VIEW - Clean, scannable overview
    # =========================================================================
    if view_mode == "📊 Table View":
        # Use application table component
        table_html = render_application_table(paginated_apps, show_url=True)
        st.markdown(table_html, unsafe_allow_html=True)

        # Add expander for each app's details below the table
        st.markdown("---")
        st.subheader("📂 Application Details")
        st.caption("Click on any application below to view full details, cover letter, and history")

        for app in paginated_apps:
            status_icon = STATUS_ICONS.get(app.status, "⚪")
            score_color = get_score_emoji(app.fit_score)
            age = days_since(app.application_date)

            with st.expander(f"{status_icon} **{app.company}** — {app.role} | {score_color} {app.fit_score or '—'}/10 | {age}", expanded=False):
                _render_application_details(app)

    # =========================================================================
    # DETAILED CARDS VIEW - Enhanced cards with summary rows
    # =========================================================================
    elif view_mode == "📋 Detailed Cards":
        for app in paginated_apps:
            # Summary row (visible without expanding)
            status_icon = STATUS_ICONS.get(app.status, "⚪")
            score_color = get_score_emoji(app.fit_score)

            # Create a more prominent summary card
            col1, col2, col3, col4, col5, col6 = st.columns([3, 3, 1.5, 0.8, 1, 0.8])

            with col1:
                st.markdown(f"### {app.company}")
            with col2:
                st.markdown(f"**{app.role or 'N/A'}**")
            with col3:
                st.markdown(f"{status_icon} **{app.status}**")
            with col4:
                if app.fit_score:
                    st.markdown(f"## {score_color} **{app.fit_score}**")
                else:
                    st.markdown("## —")
            with col5:
                age = days_since(app.application_date)
                st.write(f"📅 {format_date_short(app.application_date)}" + (f" · {age}" if age else ""))
            with col6:
                # Quick action
                if app.job_url:
                    st.markdown(f"[🔗 Link]({app.job_url})")

            # Expandable details with tabs
            with st.expander("📂 View Full Details", expanded=False):
                _render_application_details(app)

            st.markdown("---")

    # =========================================================================
    # KANBAN BOARD VIEW - Trello-style pipeline visualization
    # =========================================================================
    elif view_mode == "🎯 Kanban Board":
        st.markdown("### 🎯 Application Pipeline")
        st.caption("Visual pipeline view - Click arrows to move applications between stages")

        # Define status columns in pipeline order
        pipeline_stages = [
            {"name": "Draft", "icon": "📝", "color": "#6B7280"},
            {"name": "Applied", "icon": "📤", "color": "#F59E0B"},
            {"name": "Phone Screen", "icon": "📞", "color": "#3B82F6"},
            {"name": "Interview", "icon": "🎯", "color": "#10B981"},
            {"name": "Offer", "icon": "🎉", "color": "#059669"},
            {"name": "Accepted", "icon": "✅", "color": "#059669"},
        ]

        # Group applications by status
        from collections import defaultdict
        status_groups = defaultdict(list)
        for app in applications:  # Use all applications, not paginated
            status_groups[app.status].append(app)

        # Create columns for each stage
        num_stages = len(pipeline_stages)
        cols = st.columns(num_stages)

        for idx, stage in enumerate(pipeline_stages):
            with cols[idx]:
                status_name = stage["name"]
                apps_in_status = status_groups.get(status_name, [])
                count = len(apps_in_status)

                # Column header with count
                st.markdown(f"""
                <div style="
                    background-color: {stage['color']};
                    color: white;
                    padding: 12px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 16px;
                    font-weight: bold;
                ">
                    {stage['icon']} {status_name}<br/>
                    <span style="font-size: 1.5rem;">{count}</span>
                </div>
                """, unsafe_allow_html=True)

                # Show cards for each application in this status
                for app in apps_in_status[:10]:  # Limit to 10 per column
                    score_colors = get_score_color(app.fit_score)
                    score_display = f"{app.fit_score:.0f}" if app.fit_score else "—"

                    # Card
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background: white;
                            border: 2px solid {stage['color']};
                            border-radius: 8px;
                            padding: 12px;
                            margin-bottom: 12px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <div style="font-weight: 700; font-size: 1.1rem; color: #000; margin-bottom: 4px;">
                                {app.company}
                            </div>
                            <div style="color: #6B7280; font-size: 0.9rem; margin-bottom: 8px;">
                                {truncate(app.role or "N/A", 30)}
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="
                                    background: {score_colors['bg']};
                                    color: {score_colors['color']};
                                    padding: 4px 8px;
                                    border-radius: 12px;
                                    font-weight: 700;
                                    font-size: 0.9rem;
                                ">Score: {score_display}</span>
                                <span style="font-size: 0.8rem; color: #9CA3AF;">
                                    {format_date_short(app.application_date)}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Action buttons to move between stages
                        move_col1, move_col2 = st.columns(2)
                        with move_col1:
                            # Move backward (if not first stage)
                            if idx > 0:
                                prev_stage = pipeline_stages[idx - 1]["name"]
                                if st.button(f"← {prev_stage[:8]}", key=f"back_{app.id}", use_container_width=True):
                                    update_application(app.id, status=prev_stage)
                                    st.rerun()
                        with move_col2:
                            # Move forward (if not last stage)
                            if idx < num_stages - 1:
                                next_stage = pipeline_stages[idx + 1]["name"]
                                if st.button(f"{next_stage[:8]} →", key=f"fwd_{app.id}", use_container_width=True):
                                    update_application(app.id, status=next_stage)
                                    st.rerun()

                if count > 10:
                    st.caption(f"+ {count - 10} more...")

        # Add rejected/withdrawn at the bottom
        st.markdown("---")
        st.markdown("### 🗃️ Archived")
        rejected_col, withdrawn_col = st.columns(2)

        with rejected_col:
            rejected = status_groups.get("Rejected", [])
            st.metric("❌ Rejected", len(rejected))
            if rejected:
                with st.expander(f"View {len(rejected)} rejected"):
                    for app in rejected[:5]:
                        st.write(f"• {app.company} - {app.role or 'N/A'}")

        with withdrawn_col:
            withdrawn = status_groups.get("Withdrawn", [])
            st.metric("🚫 Withdrawn", len(withdrawn))
            if withdrawn:
                with st.expander(f"View {len(withdrawn)} withdrawn"):
                    for app in withdrawn[:5]:
                        st.write(f"• {app.company} - {app.role or 'N/A'}")

    # Bottom pagination
    if total_pages > 1 and view_mode != "🎯 Kanban Board":
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
            with pcol1:
                if st.button("◀ Previous", disabled=current_page == 0, key="prev_bottom"):
                    prev_page()
                    st.rerun()
            with pcol2:
                st.markdown(f"<div style='text-align: center'>Page {current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
            with pcol3:
                if st.button("Next ▶", disabled=current_page >= total_pages - 1, key="next_bottom"):
                    next_page()
                    st.rerun()


def show_job_insights():
    """Batch analysis and insights for all job applications."""
    st.title("📈 Job Insights & Analysis")

    with st.spinner("Analyzing all job descriptions..."):
        result = batch_analyze_all()

    if result["total_analyzed"] == 0:
        st.warning("No applications with job descriptions found. Add some applications first!")
        return

    st.success(f"Analyzed **{result['total_analyzed']}** applications with job descriptions")

    # Summary metrics
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Analyzed", result["total_analyzed"])
    with col2:
        strong = result["by_recommendation"].get("Strong Apply", 0)
        st.metric("Strong Fits", strong)
    with col3:
        apply = result["by_recommendation"].get("Apply", 0)
        st.metric("Good Fits", apply)
    with col4:
        consider = result["by_recommendation"].get("Consider", 0) + result["by_recommendation"].get("Weak Fit", 0)
        st.metric("Weak Fits", consider)

    st.markdown("---")

    # Role categories
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📁 By Role Type")
        for cat, count in result["by_category"].items():
            icon = ROLE_ICONS.get(cat, "📌")
            st.write(f"{icon} **{format_role_category(cat)}**: {count} jobs")

    with col2:
        st.subheader("📊 By Seniority")
        for sen, count in result["by_seniority"].items():
            icon = SENIORITY_ICONS.get(sen, "⚪")
            st.write(f"{icon} **{sen.title()}**: {count} jobs")

    st.markdown("---")

    # Skill analysis
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Your Strongest Skills")
        st.caption("Skills that match most job requirements")
        for skill, count in result["common_skill_matches"][:8]:
            st.write(f"• **{skill}** - matched in {count} jobs")

    with col2:
        st.subheader("⚠️ Skills to Develop")
        st.caption("Common requirements you're missing")
        for skill, count in result["common_skill_gaps"][:8]:
            st.write(f"• **{skill}** - missing in {count} jobs")

    st.markdown("---")

    # Top opportunities
    st.subheader("🏆 Best Fit Opportunities")

    # Filter by category
    categories = ["All"] + list(result["by_category"].keys())
    selected_cat = st.selectbox("Filter by Role Type", categories)

    if selected_cat == "All":
        analyses = result["all_analyses"]
    else:
        analyses = [a for a in result["all_analyses"] if a["role_category"] == selected_cat]

    # Sort option
    sort_by = st.radio("Sort by", ["Fit Score", "Company Name"], horizontal=True)
    if sort_by == "Fit Score":
        analyses = sorted(analyses, key=lambda x: x["fit_score"], reverse=True)
    else:
        analyses = sorted(analyses, key=lambda x: x["company"].lower())

    # Display
    for a in analyses:
        score_color = get_score_emoji(a["fit_score"])

        with st.expander(f"{score_color} **{a['company']}** - {a['role']} | Score: {a['fit_score']}/10 | {format_role_category(a['role_category'])}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Fit Score:** {a['fit_score']}/10")
                st.write(f"**Recommendation:** {a['recommendation']}")
                st.write(f"**Status:** {a['status']}")

            with col2:
                st.write(f"**Role Type:** {format_role_category(a['role_category'])}")
                st.write(f"**Seniority:** {a['seniority'].title()}")
                if a['experience_required']:
                    st.write(f"**Experience:** {a['experience_required']}+ years")

            with col3:
                if a['required_skills_matched']:
                    st.write("**Skills Matched:**")
                    st.write(", ".join(a['required_skills_matched'][:5]))
                if a['required_skills_gap']:
                    st.write("**Skills Gap:**")
                    st.write(", ".join(a['required_skills_gap'][:5]))


def show_email_tracking():
    """Gmail integration for tracking application emails with AI analysis."""
    st.title("📧 Email Tracking")

    # Check Gmail setup status
    setup_status = check_gmail_setup()

    # Setup status indicator
    col1, col2 = st.columns([2, 1])

    with col1:
        if setup_status['ready']:
            st.success("✅ Gmail is configured and ready!")
        else:
            st.warning("⚠️ Gmail not configured")
            st.markdown("""
            **To set up Gmail tracking:**
            1. Enable IMAP in your Gmail settings
            2. Create an App Password at: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
            3. Add to your `.env` file:
            ```
            GMAIL_EMAIL=your.email@gmail.com
            GMAIL_APP_PASSWORD=your_16_char_app_password
            ```
            4. Restart the app
            """)

    with col2:
        st.metric("Email", truncate(setup_status.get('email', 'Not set'), 20))
        st.metric("Password", "✓ Set" if setup_status['password_configured'] else "✗ Not set")

    if not setup_status['ready']:
        return

    st.markdown("---")

    # Tabs for different email features
    email_tabs = st.tabs(["🔍 Scan Emails", "🤖 AI Analysis", "🔗 Match to Applications"])

    # TAB 1: Basic email scanning
    with email_tabs[0]:
        st.subheader("🔍 Application Emails")

        last_scan = st.session_state.get('email_last_scan')
        is_first_scan = last_scan is None

        col1, col2 = st.columns([3, 1])
        with col1:
            if last_scan:
                from datetime import timezone
                now = datetime.now()
                elapsed = now - last_scan
                minutes = int(elapsed.total_seconds() / 60)
                if minutes < 60:
                    st.caption(f"Last updated {minutes} minute{'s' if minutes != 1 else ''} ago")
                else:
                    hours = int(minutes / 60)
                    st.caption(f"Last updated {hours} hour{'s' if hours != 1 else ''} ago")
            else:
                st.caption("Not yet scanned")

        scan_type = st.radio("Scan type", ["All application keywords", "Specific company"], key="scan_type", horizontal=True)
        company_search = None
        if scan_type == "Specific company":
            company_search = st.text_input("Company name to search")

        btn_label = "🔎 Scan Emails" if is_first_scan else "🔄 Update Emails"
        if is_first_scan:
            days_back = st.slider("Days to search back", 7, 90, 30, key="scan_days")
        else:
            days_back = None  # will be computed from last scan time

        if st.button(btn_label, type="primary"):
            if not is_first_scan and days_back is None:
                elapsed_days = max(1, int((datetime.now() - last_scan).total_seconds() / 86400) + 1)
                days_back = elapsed_days

            tracker = GmailTracker()
            if not tracker.connect():
                st.error("Failed to connect to Gmail")
            else:
                with st.spinner("Fetching emails..."):
                    if company_search:
                        new_emails = tracker.find_application_emails(company_search)
                    else:
                        new_emails = tracker.scan_for_responses()
                    tracker.disconnect()

                st.session_state.email_last_scan = datetime.now()

                if not is_first_scan:
                    # Merge: keep old emails, add only new ones (by id)
                    existing_ids = {e.get('id') for e in st.session_state.email_scanned_emails}
                    added = [e for e in new_emails if e.get('id') not in existing_ids]
                    st.session_state.email_scanned_emails = added + st.session_state.email_scanned_emails
                    if added:
                        st.success(f"Found **{len(added)}** new email{'s' if len(added) != 1 else ''}")
                    else:
                        st.info("No new emails since last scan")
                else:
                    st.session_state.email_scanned_emails = new_emails
                    st.success(f"Found **{len(new_emails)}** relevant emails")

        emails = st.session_state.get('email_scanned_emails', [])
        if emails:
            st.write(f"**{len(emails)} emails**")
            for email_data in emails[:30]:
                folder_badge = f"📤 {email_data.get('folder', 'Inbox')}" if email_data.get('folder') else "📥 Inbox"
                with st.expander(f"{folder_badge} **{truncate(email_data.get('subject', 'No subject'), 60)}**"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**From:** {truncate(email_data.get('from', 'Unknown'), 50)}")
                        st.write(f"**Date:** {email_data.get('date', 'Unknown')}")
                    with col2:
                        if email_data.get('id'):
                            st.write(f"**ID:** {email_data['id']}")
                    if email_data.get('snippet'):
                        st.text_area("Preview", email_data['snippet'], height=100, disabled=True, key=f"email_{email_data.get('id', 'unknown')}")

    # TAB 2: AI-powered email analysis
    with email_tabs[1]:
        st.subheader("🤖 AI Email Analysis")
        st.caption("Use AI to classify emails and extract key information like interview dates")

        col1, col2 = st.columns(2)
        with col1:
            analysis_days = st.slider("Days to analyze", 7, 60, 30, key="analysis_days")
        with col2:
            analysis_provider = st.selectbox(
                "AI Provider",
                ["auto", "groq", "google", "openai", "local"],
                help="Groq and Google are free"
            )

        if st.button("🔬 Analyze Recent Emails", type="primary"):
            tracker = GmailTracker()

            if not tracker.connect():
                st.error("Failed to connect to Gmail")
            else:
                with st.spinner("Scanning and analyzing emails with AI..."):
                    analyzed_emails = tracker.scan_and_analyze(
                        days_back=analysis_days,
                        provider=analysis_provider
                    )
                    tracker.disconnect()

                # Store in session state
                st.session_state.email_analyses = analyzed_emails

        # Display analyzed emails
        if st.session_state.get('email_analyses'):
            analyzed_emails = st.session_state.email_analyses
            st.success(f"Analyzed **{len(analyzed_emails)}** emails")

            # Group by email type
            st.markdown("### 📊 Results by Type")

            # Show priority emails first (interview invites, offers)
            priority_types = ["interview_invite", "offer", "scheduling", "info_request"]
            other_types = ["confirmation", "follow_up", "rejection", "other"]

            for email_type in priority_types + other_types:
                type_emails = [e for e in analyzed_emails if e.get('email_type') == email_type]

                if type_emails:
                    config = EMAIL_TYPE_CONFIG.get(email_type, EMAIL_TYPE_CONFIG["other"])

                    with st.expander(f"{config['icon']} {config['label']} ({len(type_emails)})", expanded=(email_type in priority_types)):
                        for email_data in type_emails:
                            st.markdown(f"**{email_data.get('subject', 'No subject')}**")

                            col1, col2, col3 = st.columns([2, 1, 1])

                            with col1:
                                st.write(f"From: {truncate(email_data.get('from', 'Unknown'), 40)}")
                                st.write(f"Date: {email_data.get('date', 'Unknown')}")

                            with col2:
                                confidence = email_data.get('confidence', 0)
                                st.write(f"Confidence: {confidence:.0%}")

                                # Show extracted date/time for interviews
                                if email_data.get('extracted_date'):
                                    st.write(f"📅 **{email_data['extracted_date']}**")
                                if email_data.get('extracted_time'):
                                    st.write(f"🕐 **{email_data['extracted_time']}**")

                            with col3:
                                suggested_status = email_data.get('suggested_status')
                                if suggested_status:
                                    st.write(f"Suggested: **{suggested_status}**")

                            # Summary
                            if email_data.get('summary'):
                                st.info(email_data['summary'])

                            # Next steps
                            next_steps = email_data.get('next_steps', [])
                            if next_steps:
                                st.markdown("**Action items:**")
                                for step in next_steps:
                                    st.markdown(f"⚡ {step}")

                            # Key details
                            key_details = email_data.get('key_details', {})
                            if key_details and any(key_details.values()):
                                details_text = []
                                if key_details.get('interviewer_name'):
                                    details_text.append(f"Interviewer: {key_details['interviewer_name']}")
                                if key_details.get('interview_format'):
                                    details_text.append(f"Format: {key_details['interview_format']}")
                                if key_details.get('location'):
                                    details_text.append(f"Location: {key_details['location']}")
                                if key_details.get('deadline'):
                                    details_text.append(f"Deadline: {key_details['deadline']}")
                                if details_text:
                                    st.caption(" | ".join(details_text))

                            st.markdown("---")

            # Action items summary
            all_action_items = []
            for email_data in analyzed_emails:
                if email_data.get('email_type') in ['interview_invite', 'offer', 'scheduling', 'info_request']:
                    for step in email_data.get('next_steps', []):
                        all_action_items.append({
                            'item': step,
                            'email': email_data.get('subject', 'Unknown'),
                            'type': email_data.get('email_type')
                        })

            if all_action_items:
                st.markdown("### ⚡ All Action Items")
                for item in all_action_items[:10]:
                    config = EMAIL_TYPE_CONFIG.get(item['type'], EMAIL_TYPE_CONFIG["other"])
                    st.markdown(f"{config['icon']} **{item['item']}** — _{truncate(item['email'], 40)}_")

    # TAB 3: Match to applications
    with email_tabs[2]:
        st.subheader("🔗 Match Emails to Applications")
        st.caption("Automatically find emails related to your tracked applications")

        if st.button("🔄 Match All Applications", type="primary"):
            tracker = GmailTracker()

            if not tracker.connect():
                st.error("Failed to connect to Gmail")
            else:
                with st.spinner("Matching emails to applications..."):
                    matches = tracker.match_emails_to_applications()
                    tracker.disconnect()

                if matches:
                    st.success(f"Found email matches for **{len(matches)}** applications")

                    for match in matches:
                        app_info = match['application']
                        emails = match['emails']

                        status_icon = STATUS_ICONS.get(app_info['status'], "⚪")

                        with st.expander(f"{status_icon} **{app_info['company']}** - {app_info['role']} ({match['email_count']} emails)"):
                            st.write(f"**Status:** {app_info['status']}")
                            st.write(f"**Total emails found:** {match['email_count']}")

                            st.markdown("**Recent emails:**")
                            for email_data in emails[:5]:
                                st.markdown(f"- 📧 {truncate(email_data.get('subject', 'No subject'), 50)} ({email_data.get('date', 'Unknown date')})")
                else:
                    st.info("No email matches found for your applications")


def show_new_application(provider: str):
    """Complete application workflow: analyze → cover letter → CV tips → save."""
    st.title("✨ New Application Workflow")

    # Initialize agent
    try:
        agent = ApplicationAgent(provider=provider)
        agent_status = agent.get_status()
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        return

    wf = st.session_state.workflow

    # Progress indicator
    steps = ["1. Job Details", "2. Analysis", "3. Cover Letter", "4. Save"]
    current_step = wf['step']

    cols = st.columns(4)
    for i, (col, step_name) in enumerate(zip(cols, steps), 1):
        if i < current_step:
            col.success(f"✅ {step_name}")
        elif i == current_step:
            col.info(f"▶️ {step_name}")
        else:
            col.write(f"⬜ {step_name}")

    st.markdown("---")

    # Reset button
    if st.button("🔄 Start New Application"):
        reset_workflow()
        st.rerun()

    # =========================================================================
    # STEP 1: JOB DETAILS INPUT
    # =========================================================================
    if current_step == 1:
        st.subheader("Step 1: Enter Job Details")

        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name *", value=wf['company'])
        with col2:
            role = st.text_input("Job Title/Role *", value=wf['role'])

        job_url = st.text_input("Job Posting URL (optional)", value=wf['job_url'])

        # Web scraper button
        if job_url and st.button("🌐 Fetch Job Description from URL", help="Auto-fetch job description from the URL"):
            with st.spinner("Scraping job posting..."):
                scraper = JobScraper()
                result = scraper.scrape_job(job_url)

                if result['success']:
                    # Auto-fill fields
                    if result.get('company') and not company:
                        wf['company'] = result['company']
                        company = result['company']
                    if result.get('role') and not role:
                        wf['role'] = result['role']
                        role = result['role']
                    if result.get('job_description'):
                        wf['job_description'] = result['job_description']

                    st.success(f"✅ Fetched from {result.get('platform', 'website')}!")
                    st.rerun()
                else:
                    st.error(f"Failed to fetch: {result.get('error', 'Unknown error')}")
                    st.info("💡 Tip: Try pasting the job description manually")

        job_description = st.text_area(
            "Job Description *",
            value=wf['job_description'],
            height=250,
            placeholder="Paste the full job description here... OR enter a URL above and click 'Fetch'"
        )

        st.markdown("---")

        if st.button("▶️ Analyze Job Fit", type="primary"):
            if company and role and job_description:
                # Save to workflow state
                wf['company'] = company
                wf['role'] = role
                wf['job_url'] = job_url
                wf['job_description'] = job_description

                # Run analysis
                with st.spinner("Analyzing job fit..."):
                    fit_analysis = agent.analyze_job_fit(job_description, force_local=True)
                    role_info = categorize_role(role, job_description)

                wf['fit_analysis'] = fit_analysis
                wf['role_category'] = role_info.get('category', 'other')
                wf['seniority'] = role_info.get('seniority', 'mid')
                wf['step'] = 2
                st.rerun()
            else:
                st.error("Please fill in Company, Role, and Job Description")

    # =========================================================================
    # STEP 2: FIT ANALYSIS RESULTS
    # =========================================================================
    elif current_step == 2:
        st.subheader("Step 2: Fit Analysis Results")

        fit = wf['fit_analysis']
        score = fit.get('fit_score', 0)

        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fit Score", f"{score}/10")
        col2.metric("Recommendation", fit.get('recommendation', 'N/A'))
        col3.metric("Role Type", format_role_category(wf['role_category']))
        col4.metric("Seniority", wf['seniority'].title() if wf['seniority'] else 'N/A')

        # Details
        col1, col2 = st.columns(2)
        with col1:
            st.success("**Your Matching Strengths:**")
            strengths = fit.get('strengths', [])
            if strengths:
                for s in strengths[:8]:
                    st.write(f"✅ {s}")
            else:
                st.write("No specific matches found")

        with col2:
            st.warning("**Skill Gaps to Address:**")
            gaps = fit.get('gaps', [])
            if gaps:
                for g in gaps[:8]:
                    st.write(f"⚠️ {g}")
            else:
                st.write("No significant gaps!")

        st.markdown("---")
        st.caption(f"Analysis: {fit.get('reasoning', 'Keyword-based matching')}")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back"):
                wf['step'] = 1
                st.rerun()
        with col2:
            if st.button("⏭️ Skip Cover Letter", type="secondary"):
                wf['step'] = 4
                st.rerun()
        with col3:
            if provider == "local":
                st.warning("Cover letter needs Groq/Google")
            else:
                if st.button("▶️ Generate Cover Letter", type="primary"):
                    wf['step'] = 3
                    st.rerun()

    # =========================================================================
    # STEP 3: COVER LETTER GENERATION
    # =========================================================================
    elif current_step == 3:
        st.subheader("Step 3: Cover Letter")
        st.info(f"Generating with **{provider}**...")

        # Generate cover letter + CV suggestions if not already done
        if wf['cover_letter'] is None:
            with st.spinner("Generating tailored cover letter..."):
                try:
                    cover_letter = agent.generate_cover_letter(
                        wf['company'], wf['role'], wf['job_description'], provider=provider
                    )
                    wf['cover_letter'] = cover_letter
                except Exception as e:
                    st.error(f"Cover letter generation failed: {e}")
                    if st.button("⬅️ Go Back"):
                        wf['step'] = 2
                        st.rerun()
                    return

            with st.spinner("Generating CV tips for this role..."):
                try:
                    cv_tips = agent.generate_cv_suggestions(
                        wf['job_description'],
                        fit_analysis=wf['fit_analysis'],
                        provider=provider
                    )
                    wf['cv_suggestions'] = cv_tips
                except Exception:
                    pass  # CV tips are optional — don't block progress

            st.rerun()

        # Display and edit cover letter
        st.write(f"**For:** {wf['company']} - {wf['role']}")

        edited_cover_letter = st.text_area(
            "Edit your cover letter:",
            value=wf['cover_letter'],
            height=350
        )
        wf['cover_letter'] = edited_cover_letter

        if wf.get('cv_suggestions'):
            with st.expander("📝 CV Tips for this role", expanded=False):
                st.markdown(wf['cv_suggestions'])

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Back"):
                wf['step'] = 2
                st.rerun()
        with col2:
            if st.button("🔄 Regenerate"):
                wf['cover_letter'] = None
                wf['cv_suggestions'] = None
                st.rerun()
        with col3:
            if st.button("▶️ Save Application", type="primary"):
                wf['step'] = 4
                st.rerun()

    # =========================================================================
    # STEP 4: SAVE APPLICATION
    # =========================================================================
    elif current_step == 4:
        st.subheader("Step 4: Save Application")

        if wf['saved_id']:
            st.success(f"✅ Application saved! ID: {wf['saved_id']}")
            st.balloons()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 View All Applications"):
                    reset_workflow()
                    # Return to the list view — without this, the rerun lands the
                    # user back on an empty wizard (app_view stays 'new_application').
                    st.session_state.app_view = 'list'
                    st.rerun()
            with col2:
                if st.button("✨ New Application"):
                    reset_workflow()
                    st.rerun()
            return

        # Summary before save
        st.write("### Application Summary")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Company:** {wf['company']}")
            st.write(f"**Role:** {wf['role']}")
            st.write(f"**Fit Score:** {wf['fit_analysis'].get('fit_score', 'N/A')}/10")
            st.write(f"**Role Type:** {format_role_category(wf['role_category'])}")

        with col2:
            st.write(f"**URL:** {wf['job_url'] or 'Not provided'}")
            st.write(f"**Cover Letter:** {'✅ Generated' if wf['cover_letter'] else '❌ Skipped'}")

        # Status selection
        save_status = st.selectbox(
            "Set initial status:",
            ["Draft", "Applied", "Saved for Later"],
            index=1
        )

        notes = st.text_area("Add notes (optional):", placeholder="Any additional notes about this application...")

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                wf['step'] = 3 if wf['cover_letter'] else 2
                st.rerun()

        with col2:
            if st.button("💾 Save Everything", type="primary"):
                with st.spinner("Saving application..."):
                    try:
                        # Save to database with all data
                        app = save_full_application(
                            company=wf['company'],
                            role=wf['role'],
                            job_description=wf['job_description'],
                            job_url=wf['job_url'] or None,
                            status=save_status,
                            fit_score=wf['fit_analysis'].get('fit_score'),
                            fit_analysis=wf['fit_analysis'],
                            role_category=wf['role_category'],
                            seniority_level=wf['seniority'],
                            cover_letter_text=wf['cover_letter'],
                            cv_suggestions=wf['cv_suggestions'],
                            notes=notes or None
                        )

                        # Also save cover letter to file if generated
                        if wf['cover_letter']:
                            cover_letters_dir = Path("data/cover_letters")
                            cover_letters_dir.mkdir(parents=True, exist_ok=True)
                            filename = f"Philipp_Goetting_Cover_Letter_{wf['company'].replace(' ', '_')}.txt"
                            filepath = cover_letters_dir / filename
                            filepath.write_text(wf['cover_letter'])

                        wf['saved_id'] = app.id
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error saving: {e}")


def show_cv_analysis(provider: str = "auto"):
    """CV Analysis page — analyses all collected job descriptions to improve the CV holistically."""
    st.title("📝 CV Analysis")
    st.caption("Analyses all your saved job descriptions together to give you targeted CV improvement recommendations.")

    # Load all job descriptions from the database
    all_apps = get_applications(limit=500)
    apps_with_jd = [a for a in all_apps if a.job_description and len(a.job_description.strip()) > 100]

    if not apps_with_jd:
        st.warning("No job descriptions saved yet. Add applications with job descriptions first.")
        return

    st.info(f"Found **{len(apps_with_jd)}** applications with job descriptions")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        min_score = st.slider("Min fit score to include (0 = all)", 0, 10, 0, key="cv_min_score")
    with col2:
        role_filter = st.multiselect(
            "Filter by role category",
            options=list({a.role_category for a in apps_with_jd if a.role_category}),
            default=[]
        )

    filtered = apps_with_jd
    if min_score > 0:
        filtered = [a for a in filtered if (a.fit_score or 0) >= min_score]
    if role_filter:
        filtered = [a for a in filtered if a.role_category in role_filter]

    if not filtered:
        st.warning("No applications match the selected filters.")
        return

    st.write(f"Analysing **{len(filtered)}** job descriptions")

    col1, col2 = st.columns([3, 1])
    with col2:
        if provider == "local":
            st.warning("Use Groq or Google for best results")

    if st.button("🔬 Analyse My CV Against All Jobs", type="primary"):
        agent = init_agent(provider)

        with st.spinner(f"Analysing {len(filtered)} job descriptions..."):
            try:
                result = agent.analyze_cv_holistic(
                    [a.job_description for a in filtered],
                    [{"company": a.company, "role": a.role, "score": a.fit_score} for a in filtered],
                    provider=provider
                )
                st.session_state.cv_analysis_result = result
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return

    if st.session_state.get('cv_analysis_result'):
        st.markdown("---")
        st.subheader("CV Improvement Recommendations")
        st.markdown(st.session_state.cv_analysis_result)

        if st.button("🔄 Re-run Analysis"):
            st.session_state.cv_analysis_result = None
            st.rerun()


def show_cv_insights(provider: str):
    """CV & Insights page: Job Insights + CV Analysis + Quick Screen in 3 tabs."""
    st.title("📝 CV & Insights")
    tab1, tab2, tab3 = st.tabs(["📈 Job Insights", "📝 CV Analysis", "🔍 Quick Screen"])
    with tab1:
        show_job_insights()
    with tab2:
        show_cv_analysis(provider)
    with tab3:
        show_quick_screen()


def show_quick_screen():
    """Quick job screening using local analysis."""
    st.title("🔍 Quick Job Screener")
    st.caption("Free & instant - uses local keyword matching (no API)")

    job_description = st.text_area(
        "Paste Job Description",
        height=300,
        placeholder="Paste any job description here to quickly check your fit..."
    )

    if st.button("Analyze", type="primary"):
        if job_description:
            from tools.local_analyzer import analyze_job_fit_local

            with st.spinner("Analyzing..."):
                result = analyze_job_fit_local(job_description)

            # Display score
            score = result.get('fit_score', 0)
            rec = result.get('recommendation', 'Unknown')

            # Color based on score
            if score >= 7:
                st.success(f"## Score: {score}/10 - {rec}")
            elif score >= 5:
                st.warning(f"## Score: {score}/10 - {rec}")
            else:
                st.error(f"## Score: {score}/10 - {rec}")

            # Details
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ Matching Skills")
                tech = result.get('technical_matches', [])
                biz = result.get('business_matches', [])
                if tech:
                    st.write("**Technical:**", ", ".join(tech))
                if biz:
                    st.write("**Business:**", ", ".join(biz))

            with col2:
                st.subheader("⚠️ Gaps")
                gaps = result.get('technical_gaps', [])
                if gaps:
                    st.write(", ".join(gaps[:10]))
                else:
                    st.write("No significant gaps!")

            # Recommendation
            st.markdown("---")
            if score >= 7:
                st.info("👉 **Worth applying!** Go to 'New Application' to generate a cover letter.")
            elif score >= 5:
                st.info("👉 **Consider applying** if you're interested in the company.")
            else:
                st.info("👉 **Weak fit** - focus on jobs that better match your skills.")
        else:
            st.warning("Please paste a job description")


def show_settings():
    """Settings and status."""
    st.title("⚙️ Settings")

    # Agent status
    st.subheader("AI Provider Status")

    try:
        agent = ApplicationAgent(provider="auto")
        status = agent.get_status()

        for provider, available in status['available_providers'].items():
            icon = "✅" if available else "❌"
            desc = {
                'local': 'Keyword matching (free, offline)',
                'groq': 'Llama 3.3 70B (free tier)',
                'google': 'Gemini 1.5 Flash (free tier)',
                'openai': 'GPT-4o-mini (paid)'
            }.get(provider, '')
            st.write(f"{icon} **{provider}**: {desc}")

        st.info(f"Active provider: **{status['active_provider']}**")

    except Exception as e:
        st.error(f"Error loading agent: {e}")

    st.markdown("---")

    # CV Summary
    st.subheader("Your CV Summary")
    cv_path = Path("data/cv_summary.txt")
    if cv_path.exists():
        cv_text = cv_path.read_text()
        new_cv = st.text_area("Edit CV Summary", cv_text, height=300)
        if st.button("Save CV Summary"):
            cv_path.write_text(new_cv)
            st.success("Saved!")

    st.markdown("---")

    # Email Automation
    st.subheader("Email Automation")

    # Check Gmail setup
    gmail_status = check_gmail_setup()

    if gmail_status['ready']:
        st.success("✓ Gmail configured and ready")

        # Get automation instance
        automation = get_automation()
        stats = automation.get_stats()

        # Display status
        col1, col2, col3 = st.columns(3)
        with col1:
            if stats['is_running']:
                st.metric("Status", "🟢 Running")
            else:
                st.metric("Status", "⚪ Stopped")

        with col2:
            st.metric("Scan Interval", f"{stats['scan_interval_minutes']} min")

        with col3:
            last_scan = stats['last_scan']
            if last_scan:
                last_scan_time = datetime.fromisoformat(last_scan)
                minutes_ago = int((datetime.now() - last_scan_time).total_seconds() / 60)
                st.metric("Last Scan", f"{minutes_ago} min ago")
            else:
                st.metric("Last Scan", "Never")

        # Stats
        st.write(f"**Total scans:** {stats['scan_count']}")
        st.write(f"**Emails processed:** {stats['emails_processed']}")
        st.write(f"**Statuses updated:** {stats['statuses_updated']}")

        # Controls
        st.markdown("**Settings:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            auto_update = st.checkbox(
                "Auto-update application status",
                value=stats['auto_update_enabled'],
                help="Automatically update application status based on email content (e.g., Interview invite → Interview status)"
            )

        with col2:
            interval = st.selectbox(
                "Scan interval (minutes)",
                options=[15, 30, 60, 120],
                index=[15, 30, 60, 120].index(stats['scan_interval_minutes']) if stats['scan_interval_minutes'] in [15, 30, 60, 120] else 1
            )

        with col3:
            notifications = st.checkbox(
                "Enable notifications",
                value=True,
                help="Get desktop notifications for important emails (interview invites, offers)"
            )

        # Action buttons
        st.markdown("**Actions:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if not stats['is_running']:
                if st.button("🚀 Start Automation", type="primary"):
                    # Update settings
                    automation.auto_update_status = auto_update
                    automation.scan_interval = interval * 60
                    automation.notifications_enabled = notifications
                    automation.notifier.enabled = notifications
                    automation.start()
                    st.success("Automation started!")
                    st.rerun()
            else:
                if st.button("⏹️ Stop Automation", type="secondary"):
                    automation.stop()
                    st.info("Automation stopped")
                    st.rerun()

        with col2:
            if st.button("🔄 Scan Now"):
                with st.spinner("Scanning emails..."):
                    result = automation.manual_scan()
                    if result['success']:
                        st.success(f"✓ Found {result['emails_found']} emails, matched {result['emails_matched']}, updated {result['statuses_updated']} statuses")
                    else:
                        st.error(f"✗ Scan failed: {result.get('error', 'Unknown error')}")
                st.rerun()

        with col3:
            if st.button("📊 View Email Analysis"):
                set_page("Email Tracking")
                st.rerun()

        # Info
        st.info("""
**How Email Automation Works:**
- Scans your Gmail inbox automatically on schedule
- Classifies emails (interview invite, rejection, offer, etc.)
- Matches emails to tracked applications
- Auto-updates application status (if enabled)
- Extracts interview dates/times from emails
        """)

    else:
        st.warning("⚠️ Gmail not configured")
        st.write("To enable email automation:")
        st.code("""
1. Enable IMAP in Gmail settings
2. Create App Password at: https://myaccount.google.com/apppasswords
3. Add to .env:
   GMAIL_EMAIL=your.email@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_password
4. Restart the app
        """)

    st.markdown("---")

    # Database info
    st.subheader("Database")
    stats = get_application_stats()
    st.write(f"Total applications: **{stats['total']}**")

    if st.button("Export to CSV"):
        import pandas as pd
        apps = get_applications(limit=1000)
        data = [{
            'company': a.company,
            'role': a.role,
            'status': a.status,
            'url': a.job_url,
            'applied': a.application_date
        } for a in apps]
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "applications.csv", "text/csv")


def show_target_companies():
    """Target company list - companies you want to apply to."""
    st.title("🎯 Target Company List")
    st.caption("Track SaaS and other companies you want to apply to")

    # Tabs
    tab1, tab2 = st.tabs(["📋 Company List", "➕ Add Company"])

    with tab1:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "Researching", "Ready", "Applied", "Not Interested"]
            )
        with col2:
            priority_filter = st.selectbox(
                "Priority",
                ["All", "High", "Medium", "Low"]
            )
        with col3:
            industry_filter = st.selectbox(
                "Industry",
                ["All", "SaaS", "FinTech", "HealthTech", "EdTech", "DevTools", "Other"]
            )

        # Get companies
        status = None if status_filter == "All" else status_filter
        priority = None if priority_filter == "All" else priority_filter
        industry = None if industry_filter == "All" else industry_filter

        companies = get_target_companies(status=status, priority=priority, industry=industry)

        if companies:
            st.markdown(f"**{len(companies)} companies found**")
            st.markdown("---")

            # Display companies
            for company in companies:
                with st.expander(f"**{company.company_name}** - {company.priority} Priority", expanded=False):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Industry:** {company.industry or 'N/A'}")
                        st.write(f"**Type:** {company.company_type or 'N/A'}")
                        st.write(f"**Size:** {company.company_size or 'N/A'}")
                        st.write(f"**Status:** {company.status}")

                        if company.website:
                            st.write(f"🔗 [Website]({company.website})")
                        if company.careers_url:
                            st.write(f"💼 [Careers Page]({company.careers_url})")
                        if company.linkedin_url:
                            st.write(f"👔 [LinkedIn]({company.linkedin_url})")

                    with col2:
                        st.write(f"**Priority:** {company.priority}")
                        st.write(f"**Applied:** {'Yes' if company.applied else 'No'}")
                        if company.applied and company.application_id:
                            st.write(f"Application ID: {company.application_id}")

                    if company.why_interested:
                        st.write(f"**Why Interested:** {company.why_interested}")

                    if company.notes:
                        st.write(f"**Notes:** {company.notes}")

                    # Actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if not company.applied:
                            if st.button("✨ Create Application", key=f"apply_{company.id}"):
                                st.info("Navigate to '✨ New Application' and use company details")
                    with col2:
                        new_status = st.selectbox(
                            "Update Status",
                            ["Researching", "Ready", "Applied", "Not Interested"],
                            index=["Researching", "Ready", "Applied", "Not Interested"].index(company.status) if company.status in ["Researching", "Ready", "Applied", "Not Interested"] else 0,
                            key=f"status_{company.id}"
                        )
                        if st.button("💾 Save Status", key=f"save_status_{company.id}"):
                            update_target_company(company.id, status=new_status)
                            st.success("Status updated!")
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_btn_company_{company.id}"):
                            st.session_state[f'confirm_delete_company_{company.id}'] = True

                    # Show confirmation if delete was clicked
                    if st.session_state.get(f'confirm_delete_company_{company.id}', False):
                        if confirm_delete(company.company_name, key=f"delete_company_{company.id}"):
                            delete_target_company(company.id)
                            st.session_state[f'confirm_delete_company_{company.id}'] = False
                            st.success(f"✅ Deleted {company.company_name}")
                            st.rerun()
        else:
            st.info("📭 No companies found. Add some companies to track!")

    with tab2:
        st.subheader("Add New Target Company")

        # Form
        with st.form("add_company_form"):
            company_name = st.text_input("Company Name*", placeholder="e.g., Notion, Stripe, Linear")

            col1, col2 = st.columns(2)
            with col1:
                industry = st.selectbox(
                    "Industry",
                    ["SaaS", "FinTech", "HealthTech", "EdTech", "DevTools", "E-commerce", "Enterprise", "Other"]
                )
                company_type = st.selectbox(
                    "Company Type",
                    ["Startup", "Scale-up", "Enterprise", "Agency"]
                )
            with col2:
                company_size = st.selectbox(
                    "Company Size",
                    ["<50", "50-200", "200-500", "500-1000", "1000+"]
                )
                priority = st.selectbox(
                    "Priority",
                    ["High", "Medium", "Low"]
                )

            website = st.text_input("Website", placeholder="https://company.com")
            careers_url = st.text_input("Careers Page URL", placeholder="https://company.com/careers")
            linkedin_url = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/company/...")

            why_interested = st.text_area(
                "Why are you interested in this company?",
                placeholder="What makes this company attractive? Product, culture, growth, tech stack...",
                height=100
            )

            notes = st.text_area(
                "Notes",
                placeholder="Any additional notes, contacts, referrals, etc.",
                height=80
            )

            submitted = st.form_submit_button("➕ Add Company", type="primary")

            if submitted:
                if company_name:
                    add_target_company(
                        company_name=company_name,
                        industry=industry,
                        company_type=company_type,
                        company_size=company_size,
                        website=website or None,
                        careers_url=careers_url or None,
                        linkedin_url=linkedin_url or None,
                        priority=priority,
                        why_interested=why_interested or None,
                        notes=notes or None
                    )
                    st.success(f"✅ {company_name} added to target list!")
                    st.rerun()
                else:
                    st.error("Company name is required!")

        st.markdown("---")

        st.subheader("📥 Import from CSV")

        csv_format = "company_name,industry,company_type,company_size,priority,website,careers_url,why_interested\nNotion,SaaS,Scale-up,200-500,High,https://notion.so,https://notion.so/careers,Great product\nLinear,SaaS,Startup,50-200,High,https://linear.app,https://linear.app/careers,Love the speed"
        st.code(csv_format, language="csv")

        uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        if uploaded_csv:
            import csv, io
            content = uploaded_csv.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(content))
            added, skipped = 0, 0
            for row in reader:
                name = (row.get("company_name") or "").strip()
                if not name:
                    skipped += 1
                    continue
                try:
                    add_target_company(
                        company_name=name,
                        industry=row.get("industry", "").strip() or None,
                        company_type=row.get("company_type", "").strip() or None,
                        company_size=row.get("company_size", "").strip() or None,
                        priority=row.get("priority", "Medium").strip() or "Medium",
                        website=row.get("website", "").strip() or None,
                        careers_url=row.get("careers_url", "").strip() or None,
                        why_interested=row.get("why_interested", "").strip() or None,
                    )
                    added += 1
                except Exception:
                    skipped += 1
            st.success(f"✅ Imported {added} companies" + (f" ({skipped} skipped)" if skipped else ""))
            st.rerun()


if __name__ == "__main__":
    main()
