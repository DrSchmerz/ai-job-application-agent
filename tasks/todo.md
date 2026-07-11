# Navigation Restructuring — 10 Pages → 5 Pages

## Steps

- [x] Step 1 — Create tasks/ directory + CLAUDE.md
- [x] Step 2 — Add `app_view` key to `init_session_state()` in `ui/utils/state.py`
- [x] Step 3 — Update sidebar navigation in `ui/app.py` (10 items → 5)
- [x] Step 4 — Add `show_applications_page()` wrapper to `ui/app.py`
- [x] Step 5 — Extract `show_job_search_tab()` from `ui/pages/workflow.py` into `ui/app.py`
- [x] Step 6 — Add `show_cv_insights()` wrapper to `ui/app.py`
- [x] Step 7 — Clean up (remove Workflow import, verify app runs)
