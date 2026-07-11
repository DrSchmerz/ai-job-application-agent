"""Serializers to convert SQLAlchemy models to JSON-serializable dicts."""
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string."""
    if dt is None:
        return None
    return dt.isoformat()


def serialize_date(d: Optional[date]) -> Optional[str]:
    """Convert date to ISO format string."""
    if d is None:
        return None
    return d.isoformat()


def serialize_application(app) -> Dict[str, Any]:
    """
    Convert an Application model to a JSON-serializable dict.

    Args:
        app: Application SQLAlchemy model instance

    Returns:
        Dict with all application fields
    """
    if app is None:
        return None

    # Parse fit_analysis_json if it exists
    fit_analysis = None
    if app.fit_analysis_json:
        try:
            fit_analysis = json.loads(app.fit_analysis_json)
        except (json.JSONDecodeError, TypeError):
            fit_analysis = None

    return {
        "id": app.id,
        "company": app.company,
        "role": app.role,
        "job_url": app.job_url,
        "job_description": app.job_description,
        "status": app.status,
        "application_date": serialize_datetime(app.application_date),
        "created_at": serialize_datetime(app.created_at),
        "fit_score": app.fit_score,
        "fit_analysis": fit_analysis,
        "role_category": app.role_category,
        "seniority_level": app.seniority_level,
        "cover_letter_text": app.cover_letter_text,
        "cv_suggestions": app.cv_suggestions,
        "cv_used": app.cv_used,
        "last_contact": serialize_date(app.last_contact),
        "notes": app.notes,
    }


def serialize_application_summary(app) -> Dict[str, Any]:
    """
    Convert an Application model to a summary dict (without large text fields).

    Args:
        app: Application SQLAlchemy model instance

    Returns:
        Dict with summary fields only
    """
    if app is None:
        return None

    return {
        "id": app.id,
        "company": app.company,
        "role": app.role,
        "status": app.status,
        "application_date": serialize_datetime(app.application_date),
        "fit_score": app.fit_score,
        "role_category": app.role_category,
        "seniority_level": app.seniority_level,
        "has_cover_letter": bool(app.cover_letter_text),
        "has_job_description": bool(app.job_description),
    }


def serialize_application_history(history) -> Dict[str, Any]:
    """
    Convert an ApplicationHistory model to a JSON-serializable dict.

    Args:
        history: ApplicationHistory SQLAlchemy model instance

    Returns:
        Dict with history event fields
    """
    if history is None:
        return None

    return {
        "id": history.id,
        "application_id": history.application_id,
        "created_at": serialize_datetime(history.created_at),
        "event_type": history.event_type,
        "old_value": history.old_value,
        "new_value": history.new_value,
        "details": history.details,
    }


def serialize_applications(apps: List) -> List[Dict[str, Any]]:
    """Serialize a list of applications to summaries."""
    return [serialize_application_summary(app) for app in apps]


def serialize_cover_letter(letter: Dict) -> Dict[str, Any]:
    """Serialize cover letter file info."""
    return {
        "name": letter.get("name"),
        "path": letter.get("path"),
        "company": letter.get("company"),
        "extension": letter.get("extension"),
    }
