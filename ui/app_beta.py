"""
Multi-user beta app (friends-beta).

Login/sign-up → upload your CV → get recommended roles + JD fit → save & track
applications, all isolated per user. Bring-your-own API key (or free local mode).

Run:  streamlit run ui/app_beta.py
"""
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import cv as cv_mod
from core import matching
from core import recommend as rec_mod
from core.providers import LLMProvider
from db import users
from db.session import SessionLocal, init_db
from ui.auth_gate import login_gate, logout_button

st.set_page_config(page_title="Job Copilot (beta)", page_icon="🚀", layout="centered")
init_db()

st.title("🚀 Job Copilot — beta")

user = login_gate()
if not user:
    st.stop()

# --- Sidebar: identity + provider (bring-your-own-key) ----------------------------
with st.sidebar:
    st.write(f"👤 **{user['email']}**")
    logout_button()
    st.divider()
    st.header("AI provider")
    provider = st.selectbox("Provider", ["auto", "local", "groq", "google", "openai"], index=0)
    api_key = st.text_input("Your API key (optional)", type="password",
                            help="Leave blank for free local matching.")

keymap = {provider: api_key} if api_key and provider in {"groq", "google", "openai"} else {}
llm = LLMProvider(keys=keymap)

find_tab, apps_tab = st.tabs(["🎯 Find roles", "📋 My applications"])

# --- Tab 1: CV -> roles + fit -----------------------------------------------------
with find_tab:
    uploaded = st.file_uploader("Upload your CV", type=["pdf", "docx", "txt", "md"])
    if uploaded:
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name
        try:
            cv_text = cv_mod.extract_text(tmp_path)
        except Exception as exc:
            cv_text = ""
            st.error(f"Could not read CV: {exc}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if cv_text:
            st.session_state["cv_text"] = cv_text
            st.success("CV loaded for this session.")

    cv_text = st.session_state.get("cv_text", "")
    if cv_text:
        st.subheader("📌 Recommended roles")
        for r in rec_mod.recommend_roles(cv_text, llm=llm, provider=provider)["recommendations"]:
            with st.container(border=True):
                st.markdown(f"**{r['title']}** — {r.get('why', '')}")

        st.subheader("🧪 Check fit for a job")
        jd = st.text_area("Paste a job description", height=150)
        if jd.strip():
            fit = matching.analyze_fit(jd, cv_text)
            st.metric("Fit score", f"{fit['fit_score']}/10 · {fit['recommendation']}")
            st.caption("Matches: " + (", ".join(fit["technical_matches"] + fit["business_matches"]) or "—"))

        st.subheader("➕ Track an application")
        with st.form("add_app"):
            company = st.text_input("Company")
            role = st.text_input("Role")
            if st.form_submit_button("Save application") and company:
                with SessionLocal() as db:
                    users.add_application(db, user["id"], company=company, role=role, status="Applied")
                st.success(f"Saved: {company} — {role}")

# --- Tab 2: per-user application list ----------------------------------------------
with apps_tab:
    with SessionLocal() as db:
        my_apps = [(a.company, a.role, a.status) for a in users.list_applications(db, user["id"])]
    if not my_apps:
        st.info("No applications yet — add one from the **Find roles** tab.")
    else:
        st.write(f"**{len(my_apps)}** application(s):")
        for company, role, status in my_apps:
            st.markdown(f"- **{company}** — {role or '—'}  ·  `{status}`")
