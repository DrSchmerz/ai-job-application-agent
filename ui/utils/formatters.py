"""
Shared formatting utilities for the UI.
"""
from datetime import datetime
from typing import Optional

# Status icons mapping - centralized to avoid duplication
STATUS_ICONS = {
    "Draft": "📝",
    "Applied": "🟡",
    "Phone Screen": "📞",
    "Technical Interview": "💻",
    "Interview": "🟢",
    "Final Round": "🎯",
    "Offer": "🎉",
    "Accepted": "✅",
    "Rejected": "🔴",
    "Withdrawn": "⬜",
    "No Response": "⏳"
}

# Event type icons
EVENT_ICONS = {
    "created": "🆕",
    "status_change": "🔄",
    "cover_letter_generated": "📝",
    "note_added": "📌",
    "email_analyzed": "📧"
}

# Role category icons
ROLE_ICONS = {
    "sales_engineer": "🎯",
    "solution_architect": "🏗️",
    "consultant": "💼",
    "data_role": "📊",
    "other": "📌"
}

# Seniority icons
SENIORITY_ICONS = {
    "senior": "⭐",
    "mid": "🔵",
    "junior": "🟢"
}


def get_score_color(score: Optional[float]) -> str:
    """
    Get color indicator for a fit score.

    Args:
        score: Fit score from 1-10

    Returns:
        Color indicator emoji
    """
    if score is None:
        return "⚪"
    if score >= 7:
        return "🟢"
    elif score >= 5:
        return "🟡"
    else:
        return "🔴"


def get_score_class(score: Optional[float]) -> str:
    """
    Get CSS class for a fit score.

    Args:
        score: Fit score from 1-10

    Returns:
        CSS class name
    """
    if score is None:
        return "score-none"
    if score >= 7:
        return "score-high"
    elif score >= 5:
        return "score-medium"
    else:
        return "score-low"


def format_date(dt: Optional[datetime], fmt: str = "%Y-%m-%d") -> str:
    """
    Format a datetime object to string.

    Args:
        dt: Datetime object or None
        fmt: Format string (default: YYYY-MM-DD)

    Returns:
        Formatted date string or "N/A"
    """
    if dt is None:
        return "N/A"
    return dt.strftime(fmt)


def format_date_short(dt: Optional[datetime]) -> str:
    """Format date as MM/DD."""
    if dt is None:
        return "—"
    return dt.strftime("%m/%d")


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime as YYYY-MM-DD HH:MM."""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


def truncate(text: Optional[str], length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text with suffix if needed
    """
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def format_role_category(category: Optional[str]) -> str:
    """Format role category for display."""
    if not category:
        return "N/A"
    return category.replace('_', ' ').title()


def format_status_with_icon(status: str) -> str:
    """Get status with its icon."""
    icon = STATUS_ICONS.get(status, "⚪")
    return f"{icon} {status}"
