"""
Reusable table components for displaying applications.
"""
from typing import List
from ui.config import get_score_color, get_status_color
from ui.utils.formatters import STATUS_ICONS, format_date_short, truncate

_TH = "padding:8px 12px;text-align:left;font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;color:#555;border-bottom:1px solid #e2e2e2;background:#f4f4f4;"
_TD = "padding:7px 12px;border-bottom:1px solid #f0f0f0;vertical-align:middle;font-size:0.85rem;color:#222;"
_TABLE = "width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e2e2;border-radius:4px;overflow:hidden;"


def _status_badge(status: str) -> str:
    color = get_status_color(status)
    icon = STATUS_ICONS.get(status, "")
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:3px;font-size:0.75rem;font-weight:500;white-space:nowrap;">'
        f'{icon} {status}</span>'
    )


def _score_badge(score) -> str:
    if not score:
        return '<span style="color:#aaa;font-size:0.82rem;">—</span>'
    sc = get_score_color(score)
    return (
        f'<span style="background:{sc["bg"]};color:{sc["color"]};'
        f'padding:2px 8px;border-radius:3px;font-size:0.78rem;font-weight:600;'
        f'border:1px solid {sc["color"]};">{score:.0f}</span>'
    )


def render_application_table(applications: List, show_url: bool = True) -> str:
    html = f'<table style="{_TABLE}"><thead><tr>'
    for h in ["Company", "Role", "Status", "Score", "Date"] + (["Link"] if show_url else []):
        html += f'<th style="{_TH}">{h}</th>'
    html += '</tr></thead><tbody>'
    for app in applications:
        html += render_application_row(app, show_url)
    html += '</tbody></table>'
    return html


def render_application_row(app, show_url: bool = True) -> str:
    url_cell = ""
    if show_url:
        if app.job_url:
            url_cell = f'<td style="{_TD}"><a href="{app.job_url}" target="_blank" style="color:#4f46e5;font-size:0.82rem;">link</a></td>'
        else:
            url_cell = f'<td style="{_TD}"><span style="color:#ccc;">—</span></td>'

    return (
        f'<tr>'
        f'<td style="{_TD}"><strong style="color:#111;">{app.company}</strong></td>'
        f'<td style="{_TD}">{truncate(app.role or "—", 50)}</td>'
        f'<td style="{_TD}">{_status_badge(app.status)}</td>'
        f'<td style="{_TD}">{_score_badge(app.fit_score)}</td>'
        f'<td style="{_TD};color:#777;">{format_date_short(app.application_date)}</td>'
        f'{url_cell}'
        f'</tr>'
    )


def render_compact_table(applications: List) -> str:
    html = f'<table style="{_TABLE}"><thead><tr>'
    for h in ["Company", "Role", "Status", "Score", "Date"]:
        html += f'<th style="{_TH}">{h}</th>'
    html += '</tr></thead><tbody>'
    for app in applications:
        html += (
            f'<tr>'
            f'<td style="{_TD}"><strong style="color:#111;">{app.company}</strong></td>'
            f'<td style="{_TD}">{truncate(app.role or "—", 40)}</td>'
            f'<td style="{_TD}">{_status_badge(app.status)}</td>'
            f'<td style="{_TD}">{_score_badge(app.fit_score)}</td>'
            f'<td style="{_TD};color:#777;">{format_date_short(app.application_date)}</td>'
            f'</tr>'
        )
    html += '</tbody></table>'
    return html
