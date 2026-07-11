"""
Centralized configuration and constants for the UI.
"""

# Theme colors
COLORS = {
    "primary": "#4F46E5",       # Indigo
    "success": "#10B981",       # Green
    "warning": "#F59E0B",       # Amber
    "danger": "#EF4444",        # Red
    "info": "#3B82F6",          # Blue
    "muted": "#6B7280",         # Gray
    "background": "#F9FAFB",    # Light gray
    "card_bg": "#FFFFFF",       # White
    "border": "#E5E7EB",        # Light border
}

# Score colors for CSS
SCORE_COLORS = {
    "high": "#10B981",     # Green for 7+
    "medium": "#F59E0B",   # Amber for 5-6
    "low": "#EF4444",      # Red for <5
    "none": "#6B7280",     # Gray for no score
}

# Status options with full list
STATUS_OPTIONS = [
    "Draft",
    "Applied",
    "Phone Screen",
    "Technical Interview",
    "Final Round",
    "Interview",
    "Offer",
    "Accepted",
    "Rejected",
    "Withdrawn",
    "No Response"
]

# Status colors for badges
STATUS_COLORS = {
    "Draft": "#6B7280",              # Gray
    "Applied": "#F59E0B",            # Amber
    "Phone Screen": "#3B82F6",       # Blue
    "Technical Interview": "#8B5CF6", # Purple
    "Final Round": "#EC4899",        # Pink
    "Interview": "#10B981",          # Green
    "Offer": "#10B981",              # Green
    "Accepted": "#059669",           # Darker green
    "Rejected": "#EF4444",           # Red
    "Withdrawn": "#9CA3AF",          # Light gray
    "No Response": "#D1D5DB",        # Very light gray
}

# Email type classifications
EMAIL_TYPES = [
    "rejection",
    "interview_invite",
    "offer",
    "scheduling",
    "info_request",
    "confirmation",
    "follow_up",
    "other"
]

# Email type display names and colors
EMAIL_TYPE_CONFIG = {
    "interview_invite": {
        "label": "Interview Invite",
        "icon": "📅",
        "color": "#10B981",
        "priority": 1
    },
    "offer": {
        "label": "Offer",
        "icon": "🎉",
        "color": "#059669",
        "priority": 2
    },
    "scheduling": {
        "label": "Scheduling",
        "icon": "📆",
        "color": "#3B82F6",
        "priority": 3
    },
    "info_request": {
        "label": "Info Request",
        "icon": "❓",
        "color": "#F59E0B",
        "priority": 4
    },
    "confirmation": {
        "label": "Confirmation",
        "icon": "✅",
        "color": "#6B7280",
        "priority": 5
    },
    "follow_up": {
        "label": "Follow-up",
        "icon": "📧",
        "color": "#6B7280",
        "priority": 6
    },
    "rejection": {
        "label": "Rejection",
        "icon": "🔴",
        "color": "#EF4444",
        "priority": 7
    },
    "other": {
        "label": "Other",
        "icon": "📋",
        "color": "#9CA3AF",
        "priority": 8
    }
}

# Pagination settings
ITEMS_PER_PAGE = 20

# Role categories
ROLE_CATEGORIES = [
    "sales_engineer",
    "solution_architect",
    "consultant",
    "data_role",
    "other"
]

# Seniority levels
SENIORITY_LEVELS = [
    "junior",
    "mid",
    "senior"
]

# Typography scale (rem values)
TYPOGRAPHY = {
    "h1": "2.5rem",
    "h2": "2rem",
    "h3": "1.5rem",
    "h4": "1.25rem",
    "body": "1rem",
    "small": "0.875rem",
    "tiny": "0.75rem"
}

# Font weights
FONT_WEIGHTS = {
    "normal": 400,
    "medium": 500,
    "semibold": 600,
    "bold": 700,
    "extrabold": 800
}

# Spacing scale (pixels) - 8px grid system
SPACING = {
    "xs": "8px",
    "sm": "16px",
    "md": "24px",
    "lg": "32px",
    "xl": "40px",
    "2xl": "48px",
    "3xl": "64px"
}

# Border radius
BORDER_RADIUS = {
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
    "full": "9999px"
}

# Shadows
SHADOWS = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
}

# Utility functions
def get_score_color(score):
    """Get color for a given fit score."""
    if score is None:
        return {"color": SCORE_COLORS["none"], "bg": "#F3F4F6"}
    if score >= 7:
        return {"color": SCORE_COLORS["high"], "bg": "#D1FAE5"}
    elif score >= 5:
        return {"color": SCORE_COLORS["medium"], "bg": "#FEF3C7"}
    else:
        return {"color": SCORE_COLORS["low"], "bg": "#FEE2E2"}

def get_status_color(status):
    """Get color for a given application status."""
    return STATUS_COLORS.get(status, COLORS["muted"])
