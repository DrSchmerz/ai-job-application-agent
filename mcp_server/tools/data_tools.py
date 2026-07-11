"""
Database MCP tools for managing job applications.

These tools handle CRUD operations on the applications database:
- List/query applications
- Get application details
- Add new applications
- Get statistics
- List cover letter files
"""
import sys
from pathlib import Path
from typing import Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.session import SessionLocal
from mcp_server.utils.serializers import (
    serialize_application,
    serialize_application_summary,
    serialize_applications,
    serialize_cover_letter,
)


def list_applications(
    status: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    List job applications with optional filters.

    Args:
        status: Filter by status (e.g., "Applied", "Interview", "Rejected", "Draft")
        company: Filter by company name (partial match, case-insensitive)
        limit: Maximum number of results (default 50)

    Returns:
        Dict with applications list and count
    """
    from tools.data_tools import get_applications

    db = SessionLocal()
    try:
        apps = get_applications(status=status, company=company, limit=limit, db=db)
        serialized = serialize_applications(apps)

        return {
            "count": len(serialized),
            "filters": {
                "status": status,
                "company": company,
                "limit": limit,
            },
            "applications": serialized,
        }
    finally:
        db.close()


def get_application(application_id: int) -> dict:
    """
    Get full details of a single application by ID.

    Args:
        application_id: The database ID of the application

    Returns:
        Dict with full application details including job description and cover letter
    """
    from tools.data_tools import get_application_by_id

    db = SessionLocal()
    try:
        app = get_application_by_id(application_id, db=db)

        if app is None:
            return {
                "success": False,
                "error": f"Application with ID {application_id} not found",
            }

        return {
            "success": True,
            "application": serialize_application(app),
        }
    finally:
        db.close()


def add_application(
    company: str,
    role: str,
    job_description: Optional[str] = None,
    job_url: Optional[str] = None,
    status: str = "Draft",
    notes: Optional[str] = None,
    fit_score: Optional[float] = None,
    role_category: Optional[str] = None,
    seniority_level: Optional[str] = None,
    cover_letter_text: Optional[str] = None,
    cv_suggestions: Optional[str] = None,
) -> dict:
    """
    Add a new job application to the database.

    Args:
        company: Company name (required)
        role: Job title/role (required)
        job_description: Full job description text
        job_url: URL to the job posting
        status: Application status (default: "Draft")
        notes: Additional notes
        fit_score: Pre-calculated fit score (1-10)
        role_category: Role type (sales_engineer, solution_architect, etc.)
        seniority_level: Seniority (junior, mid, senior)
        cover_letter_text: Generated cover letter content
        cv_suggestions: CV customization suggestions

    Returns:
        Dict with success status and created application
    """
    from tools.data_tools import save_full_application

    db = SessionLocal()
    try:
        # Build fit_analysis dict if we have a fit_score
        fit_analysis = None
        if fit_score is not None:
            fit_analysis = {"fit_score": fit_score}

        app = save_full_application(
            company=company,
            role=role,
            job_description=job_description,
            job_url=job_url,
            status=status,
            fit_score=fit_score,
            fit_analysis=fit_analysis,
            role_category=role_category,
            seniority_level=seniority_level,
            cover_letter_text=cover_letter_text,
            cv_suggestions=cv_suggestions,
            notes=notes,
            db=db,
        )

        return {
            "success": True,
            "message": f"Application created for {role} at {company}",
            "application": serialize_application_summary(app),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


def get_application_stats() -> dict:
    """
    Get summary statistics about all applications.

    Returns:
        Dict with total count and counts by status
    """
    from tools.data_tools import get_application_stats as _get_stats

    db = SessionLocal()
    try:
        stats = _get_stats(db=db)

        return {
            "total": stats.get("total", 0),
            "by_status": {
                "applied": stats.get("applied", 0),
                "interview": stats.get("interview", 0),
                "rejected": stats.get("rejected", 0),
                "offer": stats.get("offer", 0),
                "accepted": stats.get("accepted", 0),
            },
        }
    finally:
        db.close()


def list_cover_letters() -> dict:
    """
    List all saved cover letter files.

    Returns:
        Dict with list of cover letter files and their associated companies
    """
    from tools.data_tools import list_cover_letters as _list_letters

    letters = _list_letters()
    serialized = [serialize_cover_letter(letter) for letter in letters]

    return {
        "count": len(serialized),
        "cover_letters": serialized,
    }


def update_application_status(
    application_id: int,
    status: str,
    notes: Optional[str] = None
) -> dict:
    """
    Update the status of an application.

    Args:
        application_id: The database ID of the application
        status: New status. Options:
            - "Draft" - Initial state
            - "Applied" - Application submitted
            - "Phone Screen" - Phone/video screening scheduled
            - "Technical Interview" - Technical round
            - "Final Round" - Final interviews
            - "Offer" - Received offer
            - "Accepted" - Accepted offer
            - "Rejected" - Application rejected
            - "Withdrawn" - You withdrew
        notes: Optional notes to add (appends to existing notes)

    Returns:
        Dict with success status and updated application
    """
    from tools.data_tools import update_application, get_application_by_id

    db = SessionLocal()
    try:
        # Get existing application to append notes
        existing = get_application_by_id(application_id, db=db)
        if existing is None:
            return {
                "success": False,
                "error": f"Application with ID {application_id} not found",
            }

        # Append new notes to existing notes with timestamp
        final_notes = existing.notes or ""
        if notes:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            if final_notes:
                final_notes += f"\n\n[{timestamp}] Status → {status}\n{notes}"
            else:
                final_notes = f"[{timestamp}] Status → {status}\n{notes}"

        app = update_application(
            application_id=application_id,
            status=status,
            notes=final_notes if notes else None,
            db=db,
        )

        return {
            "success": True,
            "message": f"Application status updated to {status}",
            "previous_status": existing.status,
            "application": serialize_application_summary(app),
        }
    finally:
        db.close()


def add_interview_note(
    application_id: int,
    note: str,
    interview_type: Optional[str] = None,
    interviewer: Optional[str] = None,
    questions_asked: Optional[List[str]] = None
) -> dict:
    """
    Add an interview note or comment to an application.

    Use this to track interview feedback, questions asked, impressions, etc.

    Args:
        application_id: The database ID of the application
        note: The note content (required)
        interview_type: Type of interview (e.g., "Phone Screen", "Technical", "Behavioral", "Final")
        interviewer: Name/role of interviewer if known
        questions_asked: List of questions that were asked (for future prep)

    Returns:
        Dict with success status and updated notes
    """
    from tools.data_tools import get_application_by_id, add_history_event
    from db.models import Application

    db = SessionLocal()
    try:
        app = get_application_by_id(application_id, db=db)
        if app is None:
            return {
                "success": False,
                "error": f"Application with ID {application_id} not found",
            }

        # Build formatted note
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        formatted_note = f"[{timestamp}]"
        if interview_type:
            formatted_note += f" {interview_type}"
        if interviewer:
            formatted_note += f" with {interviewer}"
        formatted_note += f"\n{note}"

        if questions_asked:
            formatted_note += "\n\nQuestions Asked:"
            for q in questions_asked:
                formatted_note += f"\n  - {q}"

        # Append to existing notes
        existing_notes = app.notes or ""
        if existing_notes:
            new_notes = existing_notes + "\n\n" + formatted_note
        else:
            new_notes = formatted_note

        # Update in database
        app.notes = new_notes
        db.commit()
        db.refresh(app)

        # Add history event
        add_history_event(
            application_id=application_id,
            event_type="note_added",
            new_value=interview_type or "Note",
            details=note[:200],  # Truncate for history
            db=db,
        )

        return {
            "success": True,
            "message": "Interview note added",
            "company": app.company,
            "role": app.role,
            "note_added": formatted_note,
        }
    finally:
        db.close()


def get_application_timeline(application_id: int) -> dict:
    """
    Get the full timeline/history of an application.

    Shows all status changes, notes added, cover letters generated, etc.

    Args:
        application_id: The database ID of the application

    Returns:
        Dict with application summary and chronological history
    """
    from tools.data_tools import get_application_by_id, get_application_history
    from mcp_server.utils.serializers import serialize_application_history

    db = SessionLocal()
    try:
        app = get_application_by_id(application_id, db=db)
        if app is None:
            return {
                "success": False,
                "error": f"Application with ID {application_id} not found",
            }

        history = get_application_history(application_id, db=db)

        return {
            "success": True,
            "application": {
                "id": app.id,
                "company": app.company,
                "role": app.role,
                "current_status": app.status,
                "fit_score": app.fit_score,
                "applied_date": app.application_date.isoformat() if app.application_date else None,
            },
            "notes": app.notes,
            "history": [serialize_application_history(h) for h in history],
        }
    finally:
        db.close()
