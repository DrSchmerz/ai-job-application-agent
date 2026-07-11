"""
Unified Workflow - One page to manage your entire job search.
Integrates: Job Search → Target Companies → Apply → Track
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.job_search import JobBoardSearch, get_popular_job_boards
from tools.job_scraper import JobScraper
from db.target_companies import get_target_companies
from tools.data_tools import get_applications


def show_workflow():
    """Unified workflow page."""
    st.title("🚀 Job Search Workflow")
    st.caption("Everything you need in one place")

    # Progress indicator
    progress_col1, progress_col2, progress_col3, progress_col4 = st.columns(4)
    with progress_col1:
        st.metric("🎯 Target Companies", len(get_target_companies()))
    with progress_col2:
        apps = get_applications(limit=1000)
        st.metric("📋 Applications", len(apps))
    with progress_col3:
        applied = [a for a in apps if a.status in ["Applied", "Phone Screen", "Interview"]]
        st.metric("📤 Active", len(applied))
    with progress_col4:
        interviews = [a for a in apps if a.status in ["Phone Screen", "Interview", "Technical Interview"]]
        st.metric("🎯 Interviews", len(interviews))

    st.markdown("---")

    # Workflow tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Find Jobs",
        "🎯 Target Companies",
        "✨ Quick Apply",
        "📊 Track Progress"
    ])

    # TAB 1: Find Jobs
    with tab1:
        show_job_search()

    # TAB 2: Target Companies
    with tab2:
        show_target_companies_quick()

    # TAB 3: Quick Apply
    with tab3:
        show_quick_apply()

    # TAB 4: Track Progress
    with tab4:
        show_progress_tracker()


def show_job_search():
    """Job search section."""
    st.markdown("### 🔍 Search Job Boards")

    # Search parameters
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
        # Generate search URLs
        searcher = JobBoardSearch()
        keywords = ["SaaS", "B2B"] if saas_only else None

        search_urls = searcher.build_search_urls(
            role=role,
            location=location,
            remote=remote,
            keywords=keywords
        )

        st.success(f"✅ Generated search links for {len(search_urls)} job boards")

        # Display search links
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

    # Popular job boards
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

    # Scrape job from URL
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
                        st.success("✅ Job data saved! Go to 'Quick Apply' tab to continue.")
                else:
                    st.error(f"❌ Failed to extract job details: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a job URL")


def show_target_companies_quick():
    """Quick view of target companies."""
    st.markdown("### 🎯 Your Target Companies")

    companies = get_target_companies()

    if not companies:
        st.info("No target companies yet. Add some to get started!")
        if st.button("➕ Add Target Companies", type="primary"):
            st.switch_page("pages/target_companies.py")
        return

    # Filter by priority
    priority_filter = st.radio(
        "Priority",
        ["All", "High", "Medium", "Low"],
        horizontal=True
    )

    if priority_filter != "All":
        companies = [c for c in companies if c.priority == priority_filter]

    st.caption(f"Showing {len(companies)} companies")

    # Display companies
    for company in companies[:10]:  # Show top 10
        priority_color = {
            "High": "#ff6b6b",
            "Medium": "#feca57",
            "Low": "#48dbfb"
        }.get(company.priority, "#95afc0")

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"""
                <div style='padding: 0.5rem; border-left: 4px solid {priority_color};'>
                    <strong>{company.company_name}</strong><br>
                    <small>{company.industry or 'N/A'}</small>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.caption(company.notes[:50] + "..." if company.notes and len(company.notes) > 50 else company.notes or "")

            with col3:
                if st.button("🔍", key=f"search_{company.id}", help="Search jobs"):
                    st.session_state.job_search_company = company.company_name
                    st.info(f"Search for jobs at {company.company_name}")

    if len(companies) > 10:
        st.caption(f"+ {len(companies) - 10} more companies")


def show_quick_apply():
    """Quick apply workflow."""
    st.markdown("### ✨ Quick Apply")
    st.caption("Fast-track your application")

    # Check if we have job data from scraper
    if 'new_job_data' in st.session_state:
        job_data = st.session_state.new_job_data

        st.success("✅ Job details loaded from scraper")

        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company", value=job_data.get('company', ''))
        with col2:
            role = st.text_input("Role", value=job_data.get('role', ''))

        job_description = st.text_area(
            "Job Description",
            value=job_data.get('job_description', ''),
            height=200
        )

        if st.button("🚀 Analyze & Generate Application", type="primary", use_container_width=True):
            st.info("This would analyze fit and generate cover letter...")
            st.caption("Navigate to '✨ New Application' page for full workflow")

    else:
        st.info("👆 Import a job from the 'Find Jobs' tab or enter details manually")

        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company")
        with col2:
            role = st.text_input("Role")

        job_url = st.text_input("Job URL (optional)")
        job_description = st.text_area("Job Description", height=200)

        if st.button("🚀 Start Application", type="primary", use_container_width=True):
            if company and role:
                st.session_state.quick_apply_data = {
                    'company': company,
                    'role': role,
                    'job_url': job_url,
                    'job_description': job_description
                }
                st.success("✅ Navigate to '✨ New Application' to continue")
            else:
                st.error("Please enter company and role")


def show_progress_tracker():
    """Track application progress."""
    st.markdown("### 📊 Application Progress")

    apps = get_applications(limit=1000)

    if not apps:
        st.info("No applications yet. Start applying!")
        return

    # Status breakdown
    from collections import Counter
    status_counts = Counter([a.status for a in apps])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", len(apps))
    with col2:
        active = sum(v for k, v in status_counts.items()
                    if k not in ["Rejected", "Accepted", "Withdrawn"])
        st.metric("Active", active)
    with col3:
        interview = sum(v for k, v in status_counts.items()
                       if "Interview" in k or "Phone" in k)
        st.metric("Interviews", interview)

    # Recent activity
    st.markdown("### 📅 Recent Activity")

    recent_apps = sorted(apps, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]

    for app in recent_apps:
        days_ago = (datetime.now() - app.created_at).days if app.created_at else 0

        st.markdown(f"""
        <div style='padding: 0.5rem; background: #f8f9fa; border-radius: 5px; margin-bottom: 0.5rem;'>
            <strong>{app.company}</strong> - {app.role}<br>
            <small>Status: {app.status} • {days_ago} days ago</small>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    show_workflow()
