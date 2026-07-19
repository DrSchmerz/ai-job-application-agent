"""Reusable Streamlit login/sign-up gate for the multi-user beta.

Usage:
    user = login_gate()
    if not user:
        st.stop()
    # ... user is {"id": int, "email": str}
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.auth import validate_credentials
from db import users
from db.session import SessionLocal


def login_gate():
    """Render login/sign-up if needed. Returns the logged-in user dict, or None."""
    if st.session_state.get("user_id"):
        return {"id": st.session_state["user_id"], "email": st.session_state["user_email"]}

    st.subheader("🔐 Sign in to continue")
    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log in", use_container_width=True):
                with SessionLocal() as db:
                    user = users.authenticate(db, email, password)
                    creds = (user.id, user.email) if user else None
                if creds:
                    st.session_state["user_id"], st.session_state["user_email"] = creds
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password (min 8 chars)", type="password", key="su_pw")
            if st.form_submit_button("Create account", use_container_width=True):
                err = validate_credentials(email, password)
                if err:
                    st.error(err)
                else:
                    try:
                        with SessionLocal() as db:
                            user = users.create_user(db, email, password)
                            creds = (user.id, user.email)
                        st.session_state["user_id"], st.session_state["user_email"] = creds
                        st.rerun()
                    except users.EmailAlreadyExists:
                        st.error("That email is already registered — try logging in.")
    return None


def logout_button():
    """Render a logout button in the sidebar."""
    if st.sidebar.button("Log out"):
        for key in ("user_id", "user_email"):
            st.session_state.pop(key, None)
        st.rerun()
