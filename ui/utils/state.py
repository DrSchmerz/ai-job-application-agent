"""
Session state management for Streamlit UI.
Handles provider selection persistence and other state management.
"""
import streamlit as st
from typing import Optional

# Default provider
DEFAULT_PROVIDER = "groq"

# Available providers
PROVIDERS = ["groq", "google", "openai", "local"]


def get_provider() -> str:
    """
    Get the currently selected AI provider from session state.

    Returns:
        Provider name (groq, google, openai, local)
    """
    if 'selected_provider' not in st.session_state:
        st.session_state.selected_provider = DEFAULT_PROVIDER
    return st.session_state.selected_provider


def set_provider(provider: str) -> None:
    """
    Set the AI provider in session state.

    Args:
        provider: Provider name to set
    """
    if provider in PROVIDERS:
        st.session_state.selected_provider = provider


def get_provider_index() -> int:
    """
    Get the index of the current provider for selectbox.

    Returns:
        Index in PROVIDERS list
    """
    provider = get_provider()
    if provider in PROVIDERS:
        return PROVIDERS.index(provider)
    return 0


def init_session_state() -> None:
    """Initialize all session state variables."""
    # Provider
    if 'selected_provider' not in st.session_state:
        st.session_state.selected_provider = DEFAULT_PROVIDER

    # Agent instance
    if 'agent' not in st.session_state:
        st.session_state.agent = None

    # Cover letter (legacy)
    if 'cover_letter' not in st.session_state:
        st.session_state.cover_letter = None

    # Workflow state for new applications
    if 'workflow' not in st.session_state:
        st.session_state.workflow = {
            'step': 1,
            'company': '',
            'role': '',
            'job_url': '',
            'job_description': '',
            'fit_analysis': None,
            'role_category': None,
            'seniority': None,
            'cover_letter': None,
            'cv_suggestions': None,
            'saved_id': None
        }

    # Applications view: 'list' or 'new_application'
    if 'app_view' not in st.session_state:
        st.session_state.app_view = 'list'

    # Pagination state
    if 'applications_page' not in st.session_state:
        st.session_state.applications_page = 0

    # Email analysis state
    if 'email_analyses' not in st.session_state:
        st.session_state.email_analyses = []
    if 'email_last_scan' not in st.session_state:
        st.session_state.email_last_scan = None
    if 'email_scanned_emails' not in st.session_state:
        st.session_state.email_scanned_emails = []
    if 'cv_analysis_result' not in st.session_state:
        st.session_state.cv_analysis_result = None


def reset_workflow() -> None:
    """Reset the application workflow state."""
    st.session_state.workflow = {
        'step': 1,
        'company': '',
        'role': '',
        'job_url': '',
        'job_description': '',
        'fit_analysis': None,
        'role_category': None,
        'seniority': None,
        'cover_letter': None,
        'cv_suggestions': None,
        'saved_id': None
    }


def get_page() -> int:
    """Get current applications page number."""
    return st.session_state.get('applications_page', 0)


def set_page(page: int) -> None:
    """Set applications page number."""
    st.session_state.applications_page = max(0, page)


def next_page() -> None:
    """Go to next page."""
    st.session_state.applications_page = get_page() + 1


def prev_page() -> None:
    """Go to previous page."""
    st.session_state.applications_page = max(0, get_page() - 1)
