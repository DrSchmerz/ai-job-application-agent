"""
Custom CSS styles for the Streamlit UI — minimal, technical aesthetic.
"""
import streamlit as st


def inject_custom_styles() -> None:
    """Inject custom CSS styles into the Streamlit app."""
    st.markdown("""
    <style>
    /* ── Base ───────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-size: 14px !important;
        background-color: #fafafa !important;
    }

    .stApp, .main {
        background-color: #fafafa !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        background-color: #fafafa !important;
    }

    /* ── Typography ─────────────────────────────────────────────────── */
    h1 {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #111 !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: -0.01em !important;
    }

    h2 {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #111 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
    }

    h3 {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #111 !important;
    }

    p, div, span, label, .stMarkdown {
        font-size: 0.875rem !important;
        line-height: 1.5 !important;
        color: #333 !important;
    }

    .stCaption, small {
        font-size: 0.78rem !important;
        color: #777 !important;
    }

    /* ── Sidebar ─────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] > div {
        background-color: #f4f4f4 !important;
        border-right: 1px solid #e2e2e2 !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: #333 !important;
    }

    /* ── Buttons ─────────────────────────────────────────────────────── */
    .stButton > button {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 5px 14px !important;
        border-radius: 4px !important;
        border: 1px solid #d0d0d0 !important;
        background-color: #fff !important;
        color: #333 !important;
        transition: background 0.15s ease !important;
        box-shadow: none !important;
    }

    .stButton > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #aaa !important;
    }

    .stButton > button[kind="primary"] {
        background-color: #4f46e5 !important;
        color: #fff !important;
        border-color: #4338ca !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #4338ca !important;
    }

    /* ── Inputs ──────────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        font-size: 0.85rem !important;
        padding: 6px 10px !important;
        border-radius: 4px !important;
        border: 1px solid #d8d8d8 !important;
        background-color: #fff !important;
        color: #111 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1) !important;
    }

    /* ── Metrics ─────────────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: #fff !important;
        border: 1px solid #e2e2e2 !important;
        border-radius: 4px !important;
        padding: 12px 16px !important;
        box-shadow: none !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #111 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: #666 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }

    /* ── Expanders ───────────────────────────────────────────────────── */
    .stExpander {
        border: 1px solid #e2e2e2 !important;
        border-radius: 4px !important;
        margin-bottom: 6px !important;
        background-color: #fff !important;
        box-shadow: none !important;
    }

    .stExpander > div:first-child {
        padding: 8px 12px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        background-color: #fff !important;
        border-radius: 4px !important;
    }

    /* ── Tabs ────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
        border-bottom: 1px solid #e2e2e2 !important;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 6px 14px !important;
        border-radius: 4px 4px 0 0 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    /* ── Alerts ──────────────────────────────────────────────────────── */
    .stAlert {
        padding: 8px 12px !important;
        border-radius: 4px !important;
        font-size: 0.82rem !important;
    }

    .stSuccess, .stInfo, .stWarning, .stError {
        font-size: 0.82rem !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        font-weight: 400 !important;
    }

    /* ── Status badges ───────────────────────────────────────────────── */
    .status-badge {
        display: inline-block;
        padding: 2px 8px !important;
        border-radius: 3px !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: white !important;
        letter-spacing: 0.01em !important;
    }

    .status-draft              { background-color: #9ca3af; }
    .status-applied            { background-color: #f59e0b; }
    .status-phone-screen       { background-color: #3b82f6; }
    .status-technical-interview{ background-color: #8b5cf6; }
    .status-final-round        { background-color: #ec4899; }
    .status-interview          { background-color: #10b981; }
    .status-offer              { background-color: #10b981; }
    .status-accepted           { background-color: #059669; }
    .status-rejected           { background-color: #ef4444; }
    .status-withdrawn          { background-color: #9ca3af; }
    .status-no-response        { background-color: #e5e7eb; color: #374151 !important; }

    /* ── Score indicator ─────────────────────────────────────────────── */
    .score-indicator {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px !important;
        height: 28px !important;
        border-radius: 50% !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        border: 1px solid !important;
    }

    .score-high   { background-color: #d1fae5; color: #065f46; border-color: #10b981 !important; }
    .score-medium { background-color: #fef3c7; color: #92400e; border-color: #f59e0b !important; }
    .score-low    { background-color: #fee2e2; color: #991b1b; border-color: #ef4444 !important; }
    .score-none   { background-color: #f3f4f6; color: #6b7280; border-color: #d1d5db !important; }

    /* ── Email type badges ───────────────────────────────────────────── */
    .email-type-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px !important;
        padding: 2px 8px !important;
        border-radius: 3px !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
    }

    .email-interview-invite { background-color: #d1fae5; color: #065f46; }
    .email-offer            { background-color: #d1fae5; color: #065f46; }
    .email-scheduling       { background-color: #dbeafe; color: #1e40af; }
    .email-info-request     { background-color: #fef3c7; color: #92400e; }
    .email-rejection        { background-color: #fee2e2; color: #991b1b; }
    .email-confirmation     { background-color: #f3f4f6; color: #374151; }
    .email-other            { background-color: #f3f4f6; color: #6b7280; }

    /* ── Confidence bar ──────────────────────────────────────────────── */
    .confidence-bar {
        width: 100%;
        height: 4px !important;
        background-color: #e5e7eb;
        border-radius: 2px !important;
        overflow: hidden;
    }

    .confidence-fill {
        height: 100%;
        background-color: #4f46e5;
        border-radius: 2px !important;
    }

    /* ── App table ───────────────────────────────────────────────────── */
    .app-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem !important;
        background-color: #fff;
        border: 1px solid #e2e2e2;
        border-radius: 4px;
        overflow: hidden;
    }

    .app-table thead { background: #f4f4f4; }

    .app-table th {
        padding: 8px 12px !important;
        text-align: left;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #555 !important;
        border-bottom: 1px solid #e2e2e2;
    }

    .app-table tbody tr { border-bottom: 1px solid #f0f0f0; }
    .app-table tbody tr:hover { background-color: #f8f8f8 !important; }
    .app-table tbody tr:last-child { border-bottom: none; }

    .app-table td {
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
        color: #222 !important;
        font-weight: 400 !important;
    }

    /* ── Misc ────────────────────────────────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }

    ::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
    ::-webkit-scrollbar-track { background: #f0f0f0; }
    ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px !important; }
    ::-webkit-scrollbar-thumb:hover { background: #aaa; }

    /* Radio buttons */
    .stRadio > label, .stCheckbox > label {
        font-size: 0.85rem !important;
        font-weight: 400 !important;
        color: #333 !important;
    }

    /* Action item */
    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 8px !important;
        padding: 6px 10px !important;
        background-color: #fffbeb !important;
        border-left: 3px solid #f59e0b !important;
        border-radius: 0 3px 3px 0 !important;
        margin-bottom: 4px !important;
        font-size: 0.82rem !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    status_class = status.lower().replace(" ", "-").replace("_", "-")
    return f'<span class="status-badge status-{status_class}">{status}</span>'


def render_score_indicator(score) -> str:
    if score is None:
        return '<span class="score-indicator score-none">—</span>'
    if score >= 7:
        cls = "score-high"
    elif score >= 5:
        cls = "score-medium"
    else:
        cls = "score-low"
    return f'<span class="score-indicator {cls}">{score:.0f}</span>'


def render_confidence_bar(confidence: float) -> str:
    pct = int(confidence * 100)
    return f'''
    <div class="confidence-bar">
        <div class="confidence-fill" style="width:{pct}%"></div>
    </div>
    <span style="font-size:0.75rem;color:#777">{pct}%</span>
    '''


def render_action_item(item: str) -> str:
    return f'''
    <div class="action-item">
        <span>⚡</span>
        <span>{item}</span>
    </div>
    '''
