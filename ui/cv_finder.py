"""
CV & Role Finder — a self-contained demo of the multi-user product flow.

Upload a CV → get recommended roles to target → screen a job description for fit.
Works with no API key (local skill matching) or with a user-provided key
(bring-your-own-key), which is the model for a future multi-user version.

Run:  streamlit run ui/cv_finder.py
"""
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import cv as cv_mod
from core import recommend as rec_mod
from core import matching
from core.providers import LLMProvider

st.set_page_config(page_title="CV & Role Finder", page_icon="🎯", layout="centered")
st.title("🎯 CV & Role Finder")
st.caption("Upload your CV → get roles to target → check your fit for a specific job.")

# --- Sidebar: bring-your-own-key --------------------------------------------------
with st.sidebar:
    st.header("AI provider")
    st.write("Leave blank to use free local matching, or paste a key for AI-powered results.")
    provider = st.selectbox("Provider", ["auto", "local", "groq", "google", "openai"], index=0)
    key = st.text_input("API key (optional)", type="password")

keymap = {}
if key and provider in {"groq", "google", "openai"}:
    keymap[provider] = key
llm = LLMProvider(keys=keymap) if keymap else LLMProvider(keys={})

# --- CV upload --------------------------------------------------------------------
uploaded = st.file_uploader("Upload your CV", type=["pdf", "docx", "txt", "md"])
cv_text = ""
if uploaded:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name
    try:
        cv_text = cv_mod.extract_text(tmp_path)
    except Exception as exc:
        st.error(f"Could not read CV: {exc}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

if cv_text:
    profile = cv_mod.parse_cv(cv_text, llm=llm, provider=provider)
    st.success(f"CV parsed ({profile.get('source')} mode).")
    if profile.get("skills"):
        st.write("**Detected skills:** " + ", ".join(profile["skills"][:25]))

    st.subheader("📌 Recommended roles to target")
    recs = rec_mod.recommend_roles(cv_text, llm=llm, provider=provider, top_n=5)
    if not recs["recommendations"]:
        st.info("No confident role matches — try adding more detail to your CV.")
    for r in recs["recommendations"]:
        with st.container(border=True):
            st.markdown(f"**{r['title']}**")
            st.caption(r.get("why", ""))
            terms = r.get("search_terms", [])
            if terms:
                st.write("🔎 Search terms: " + " · ".join(f"`{t}`" for t in terms))

    st.subheader("🧪 Check fit for a specific job")
    jd = st.text_area("Paste a job description", height=180)
    if jd.strip():
        fit = matching.analyze_fit(jd, cv_text)
        c1, c2 = st.columns(2)
        c1.metric("Fit score", f"{fit['fit_score']}/10")
        c2.metric("Recommendation", fit["recommendation"])
        st.write("✅ **Matches:** " + (", ".join(fit["technical_matches"] + fit["business_matches"]) or "—"))
        st.write("❌ **Gaps:** " + (", ".join(fit["technical_gaps"] + fit["business_gaps"]) or "—"))
else:
    st.info("👆 Upload a CV to get started. No data is stored — everything runs in this session.")
