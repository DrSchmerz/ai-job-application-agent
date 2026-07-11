"""
Data utility functions for the AI Application Agent.
These tools help load CV, cover letters, and manage application tracking.
"""
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from db.models import Application, ApplicationHistory
from db.session import SessionLocal


# File paths
PROJECT_ROOT = Path(__file__).parent.parent
CV_DIR = PROJECT_ROOT / "data" / "cv"
COVER_LETTER_DIR = PROJECT_ROOT / "data" / "cover_letters"
JOB_URLS_FILE = PROJECT_ROOT / "data" / "job_urls.txt"


def load_cv_path() -> Optional[Path]:
    """
    Get the path to the most recent CV file.

    Returns:
        Path to CV file or None if not found
    """
    if not CV_DIR.exists():
        return None

    # Get all PDF files in CV directory
    cv_files = list(CV_DIR.glob("*.pdf"))

    if not cv_files:
        return None

    # Return the most recently modified CV
    return max(cv_files, key=lambda p: p.stat().st_mtime)


def load_cv_content() -> Optional[bytes]:
    """
    Load the CV file content as bytes.
    Useful for uploading or processing.

    Returns:
        CV file content as bytes or None if not found
    """
    cv_path = load_cv_path()
    if cv_path and cv_path.exists():
        return cv_path.read_bytes()
    return None


def list_cover_letters() -> List[Dict[str, str]]:
    """
    List all cover letters in the cover_letters directory.

    Returns:
        List of dicts with 'name', 'path', and 'company' (extracted from filename)
    """
    if not COVER_LETTER_DIR.exists():
        return []

    cover_letters = []

    for file_path in COVER_LETTER_DIR.glob("*"):
        if file_path.is_file():
            # Try to extract company name from filename
            # e.g., "Philipp_Goetting_Cover_Letter_MongoDB.pdf" -> "MongoDB"
            filename = file_path.stem
            parts = filename.split("_")

            # Look for "Cover" and "Letter" in parts, company comes after
            company = "Unknown"
            for i, part in enumerate(parts):
                if part == "Letter" and i + 1 < len(parts):
                    company = "_".join(parts[i+1:])
                    break

            cover_letters.append({
                "name": file_path.name,
                "path": str(file_path),
                "company": company,
                "extension": file_path.suffix
            })

    return sorted(cover_letters, key=lambda x: x["company"])


def get_cover_letter_for_company(company: str) -> Optional[Path]:
    """
    Find a cover letter for a specific company.

    Args:
        company: Company name (case-insensitive)

    Returns:
        Path to cover letter or None if not found
    """
    company_lower = company.lower()

    for letter in list_cover_letters():
        if company_lower in letter["company"].lower():
            return Path(letter["path"])

    return None


def load_job_urls() -> List[str]:
    """
    Load all job posting URLs from the job_urls.txt file.

    Returns:
        List of job URLs
    """
    if not JOB_URLS_FILE.exists():
        return []

    with open(JOB_URLS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def add_application(
    company: str,
    role: str,
    job_url: Optional[str] = None,
    job_description: Optional[str] = None,
    status: str = "Applied",
    cv_used: Optional[str] = None,
    cover_letter: Optional[str] = None,
    notes: Optional[str] = None,
    db: Optional[Session] = None
) -> Application:
    """
    Add a new application to the database.

    Args:
        company: Company name
        role: Job title/role
        job_url: URL to job posting
        job_description: Full job description text
        status: Application status (default: "Applied")
        cv_used: Path to CV used
        cover_letter: Path to cover letter used
        notes: Additional notes
        db: Database session (creates new one if not provided)

    Returns:
        The created Application object
    """
    # Create session if not provided
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        application = Application(
            company=company,
            role=role,
            job_url=job_url,
            job_description=job_description,
            status=status,
            application_date=datetime.now(),
            cv_used=cv_used,
            cover_letter=cover_letter,
            notes=notes
        )

        db.add(application)
        db.commit()
        db.refresh(application)

        # If we're closing the session, expunge (detach) the object
        # This allows it to be used after the session closes (read-only)
        if close_session:
            db.expunge(application)

        return application

    finally:
        if close_session:
            db.close()


def save_full_application(
    company: str,
    role: str,
    job_description: str,
    job_url: Optional[str] = None,
    status: str = "Draft",
    fit_score: Optional[float] = None,
    fit_analysis: Optional[Dict] = None,
    role_category: Optional[str] = None,
    seniority_level: Optional[str] = None,
    cover_letter_text: Optional[str] = None,
    cv_suggestions: Optional[str] = None,
    notes: Optional[str] = None,
    db: Optional[Session] = None
) -> Application:
    """
    Save a complete application with all analysis and generated content.

    Args:
        company: Company name
        role: Job title/role
        job_description: Full job description text
        job_url: URL to job posting
        status: Application status (default: "Draft")
        fit_score: Calculated fit score (1-10)
        fit_analysis: Dict with matched skills, gaps, recommendation
        role_category: sales_engineer, solution_architect, etc.
        seniority_level: junior, mid, senior
        cover_letter_text: Generated cover letter content
        cv_suggestions: CV customization suggestions
        notes: Additional notes

    Returns:
        The created Application object
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        application = Application(
            company=company,
            role=role,
            job_url=job_url,
            job_description=job_description,
            status=status,
            application_date=datetime.now() if status != "Draft" else None,
            created_at=datetime.now(),
            fit_score=fit_score,
            fit_analysis_json=json.dumps(fit_analysis) if fit_analysis else None,
            role_category=role_category,
            seniority_level=seniority_level,
            cover_letter_text=cover_letter_text,
            cv_suggestions=cv_suggestions,
            notes=notes
        )

        db.add(application)
        db.commit()
        db.refresh(application)

        # Add history entry
        add_history_event(
            application_id=application.id,
            event_type="created",
            new_value=status,
            details=f"Application created for {role} at {company}",
            db=db
        )

        # Load all data we need before closing session
        app_id = application.id
        app_company = application.company
        app_role = application.role

        # If we're closing the session, expunge (detach) the object
        # This allows it to be used after the session closes (read-only)
        if close_session:
            db.expunge(application)

        return application

    finally:
        if close_session:
            db.close()


def update_application(
    application_id: int,
    status: Optional[str] = None,
    fit_score: Optional[float] = None,
    fit_analysis: Optional[Dict] = None,
    role_category: Optional[str] = None,
    seniority_level: Optional[str] = None,
    cover_letter_text: Optional[str] = None,
    cv_suggestions: Optional[str] = None,
    notes: Optional[str] = None,
    db: Optional[Session] = None
) -> Optional[Application]:
    """
    Update an existing application with new data.
    Automatically tracks changes in history.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return None

        # Track status changes
        if status and status != app.status:
            add_history_event(
                application_id=application_id,
                event_type="status_change",
                old_value=app.status,
                new_value=status,
                db=db
            )
            app.status = status
            if status == "Applied" and not app.application_date:
                app.application_date = datetime.now()

        # Update other fields
        if fit_score is not None:
            app.fit_score = fit_score
        if fit_analysis is not None:
            app.fit_analysis_json = json.dumps(fit_analysis)
        if role_category is not None:
            app.role_category = role_category
        if seniority_level is not None:
            app.seniority_level = seniority_level
        if cover_letter_text is not None:
            if not app.cover_letter_text:  # First time generating
                add_history_event(
                    application_id=application_id,
                    event_type="cover_letter_generated",
                    new_value="Cover letter created",
                    db=db
                )
            app.cover_letter_text = cover_letter_text
        if cv_suggestions is not None:
            app.cv_suggestions = cv_suggestions
        if notes is not None:
            app.notes = notes

        db.commit()
        db.refresh(app)
        return app

    finally:
        if close_session:
            db.close()


def add_history_event(
    application_id: int,
    event_type: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    details: Optional[str] = None,
    db: Optional[Session] = None
) -> ApplicationHistory:
    """Add a history event for an application."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        event = ApplicationHistory(
            application_id=application_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value,
            details=details,
            created_at=datetime.now()
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        if close_session:
            db.close()


def get_application_by_id(application_id: int, db: Optional[Session] = None) -> Optional[Application]:
    """Get a single application by ID with all its data."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        return db.query(Application).filter(Application.id == application_id).first()
    finally:
        if close_session:
            db.close()


def get_application_history(application_id: int, db: Optional[Session] = None) -> List[ApplicationHistory]:
    """Get all history events for an application."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        return db.query(ApplicationHistory).filter(
            ApplicationHistory.application_id == application_id
        ).order_by(ApplicationHistory.created_at.desc()).all()
    finally:
        if close_session:
            db.close()


def get_successful_applications(db: Optional[Session] = None) -> List[Application]:
    """Get applications that resulted in interviews or offers (for learning)."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        return db.query(Application).filter(
            Application.status.in_(["Interview", "Offer", "Accepted", "Phone Screen", "Technical Interview", "Final Round"])
        ).all()
    finally:
        if close_session:
            db.close()


def get_applications(
    status: Optional[str] = None,
    company: Optional[str] = None,
    limit: Optional[int] = None,
    db: Optional[Session] = None
) -> List[Application]:
    """
    Query applications from the database.

    Args:
        status: Filter by status (e.g., "Applied", "Interview", "Rejected")
        company: Filter by company name (partial match)
        limit: Maximum number of results
        db: Database session (creates new one if not provided)

    Returns:
        List of Application objects
    """
    # Create session if not provided
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        query = db.query(Application)

        if status:
            query = query.filter(Application.status == status)

        if company:
            query = query.filter(Application.company.ilike(f"%{company}%"))

        # Order by most recent first
        query = query.order_by(Application.application_date.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    finally:
        if close_session:
            db.close()


def get_application_stats(db: Optional[Session] = None) -> Dict[str, int]:
    """
    Get statistics about applications in the database.

    Args:
        db: Database session (creates new one if not provided)

    Returns:
        Dict with counts by status
    """
    # Create session if not provided
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        total = db.query(Application).count()

        # Get count by status
        stats = {"total": total}

        statuses = ["Applied", "Interview", "Rejected", "Offer", "Accepted"]
        for status in statuses:
            count = db.query(Application).filter(Application.status == status).count()
            stats[status.lower()] = count

        return stats

    finally:
        if close_session:
            db.close()


# Example usage and tests
if __name__ == "__main__":
    print("🔧 Testing Data Tools\n")

    print("📄 CV:")
    cv_path = load_cv_path()
    if cv_path:
        print(f"  Found: {cv_path.name}")
    else:
        print("  Not found")

    print("\n📝 Cover Letters:")
    letters = list_cover_letters()
    for letter in letters[:5]:  # Show first 5
        print(f"  - {letter['company']}: {letter['name']}")

    print(f"\n  Total: {len(letters)} cover letters")

    print("\n🔗 Job URLs:")
    urls = load_job_urls()
    print(f"  Total: {len(urls)} URLs loaded")

    print("\n📊 Application Stats:")
    stats = get_application_stats()
    print(f"  Total applications: {stats['total']}")
    for status, count in stats.items():
        if status != 'total':
            print(f"  {status.capitalize()}: {count}")
