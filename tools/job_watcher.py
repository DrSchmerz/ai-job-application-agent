"""
Target-company job watcher.

Checks the public JSON APIs of Greenhouse and Lever job boards for every company
in the target list, scores each posting against your CV (local matching, no API
key needed), and stores discoveries in the ``job_postings`` table so new ones
can be highlighted.

No scraping of LinkedIn/Indeed — only the stable, officially public board APIs:
  Greenhouse: https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true
  Lever:      https://api.lever.co/v0/postings/<slug>?mode=json  (+ EU host)
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logging_config import get_logger
from core.matching import analyze_fit

log = get_logger(__name__)

TIMEOUT = 15
MAX_DESCRIPTION_CHARS = 4000

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
LEVER_APIS = [
    "https://api.lever.co/v0/postings/{slug}?mode=json",
    "https://api.eu.lever.co/v0/postings/{slug}?mode=json",  # EU-hosted boards
]


# --- board detection ----------------------------------------------------------------

def parse_board_from_url(url: str) -> Optional[Tuple[str, str]]:
    """Extract (source, token) from a careers URL if it's a Greenhouse/Lever board."""
    if not url:
        return None
    url = url.lower()
    m = re.search(r"greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)", url)
    if m and m.group(1) not in {"boards", "job-boards", "boards-api"}:
        return ("greenhouse", m.group(1))
    m = re.search(r"lever\.co/([a-z0-9_-]+)", url)
    if m and m.group(1) not in {"jobs", "api", "www"}:
        return ("lever", m.group(1))
    return None


def slug_candidates(company_name: str) -> List[str]:
    """Likely board tokens for a company name: 'The Trade Desk' -> thetradedesk, the-trade-desk."""
    words = re.findall(r"[a-z0-9]+", (company_name or "").lower())
    if not words:
        return []
    candidates = ["".join(words)]
    if len(words) > 1:
        candidates.append("-".join(words))
    return candidates


def _strip_html(html: str) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


# --- fetchers -----------------------------------------------------------------------

def fetch_greenhouse(token: str) -> Optional[List[Dict]]:
    """Fetch postings from a Greenhouse board. None = board doesn't exist/unreachable."""
    try:
        resp = requests.get(GREENHOUSE_API.format(token=token), timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        jobs = resp.json().get("jobs", [])
    except (requests.RequestException, ValueError):
        return None
    return [
        {
            "source": "greenhouse",
            "external_id": str(j.get("id", "")),
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "description": _strip_html(j.get("content", ""))[:MAX_DESCRIPTION_CHARS],
        }
        for j in jobs
    ]


def fetch_lever(slug: str) -> Optional[List[Dict]]:
    """Fetch postings from a Lever board (tries US then EU host)."""
    for api in LEVER_APIS:
        try:
            resp = requests.get(api.format(slug=slug), timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            jobs = resp.json()
            if not isinstance(jobs, list):
                continue
        except (requests.RequestException, ValueError):
            continue
        return [
            {
                "source": "lever",
                "external_id": str(j.get("id", "")),
                "title": j.get("text", ""),
                "location": ((j.get("categories") or {}).get("location") or ""),
                "url": j.get("hostedUrl", ""),
                # descriptionPlain is only the intro; the actual JD body is in
                # descriptionBodyPlain (with extras in additionalPlain)
                "description": " ".join(
                    part for part in (
                        j.get("descriptionPlain"),
                        j.get("descriptionBodyPlain"),
                        j.get("additionalPlain"),
                    ) if part
                )[:MAX_DESCRIPTION_CHARS],
            }
            for j in jobs
        ]
    return None


def find_board(company_name: str, careers_url: str = "") -> Optional[Tuple[str, str, List[Dict]]]:
    """Locate a company's board and fetch its postings.

    Returns (source, token, postings) or None. The careers_url (if it points at a
    Greenhouse/Lever board) wins; otherwise name-derived slugs are tried.
    """
    attempts: List[Tuple[str, str]] = []
    hinted = parse_board_from_url(careers_url)
    if hinted:
        attempts.append(hinted)
    for slug in slug_candidates(company_name):
        attempts.extend([("greenhouse", slug), ("lever", slug)])

    tried = set()
    for source, token in attempts:
        if (source, token) in tried:
            continue
        tried.add((source, token))
        postings = fetch_greenhouse(token) if source == "greenhouse" else fetch_lever(token)
        if postings is not None:
            return (source, token, postings)
    return None


# --- persistence + scoring ----------------------------------------------------------

def upsert_postings(db, company: str, postings: List[Dict], cv_text: str) -> Dict[str, int]:
    """Store postings for a company; returns {'new': n, 'seen': n}.

    New postings get a fit score against the CV. Postings no longer on the
    board are marked inactive.
    """
    from db.models import JobPosting

    now = datetime.utcnow()
    counts = {"new": 0, "seen": 0}
    live_ids = set()

    for p in postings:
        if not p["external_id"]:
            continue
        live_ids.add((p["source"], p["external_id"]))
        existing = (
            db.query(JobPosting)
            .filter(
                JobPosting.source == p["source"],
                JobPosting.external_id == p["external_id"],
            )
            .first()
        )
        if existing:
            existing.last_seen = now
            existing.is_active = 1
            counts["seen"] += 1
            continue

        fit = None
        if cv_text:
            result = analyze_fit(f"{p['title']}\n{p['description']}", cv_text)
            fit = float(result.get("fit_score") or 0)

        db.add(JobPosting(
            company=company,
            source=p["source"],
            external_id=p["external_id"],
            title=p["title"][:300],
            location=(p.get("location") or "")[:200],
            url=p.get("url", ""),
            description=p.get("description", ""),
            fit_score=fit,
            first_seen=now,
            last_seen=now,
        ))
        counts["new"] += 1

    # Mark this company's postings that vanished from the board as inactive
    for row in db.query(JobPosting).filter(JobPosting.company == company, JobPosting.is_active == 1):
        if (row.source, row.external_id) not in live_ids:
            row.is_active = 0

    db.commit()
    return counts


def check_target_companies() -> Dict:
    """Check every target company's board for postings. Returns a summary dict."""
    from db.session import SessionLocal
    from db.target_companies import TargetCompany
    from tools.local_analyzer import load_cv_summary

    cv_text = load_cv_summary()
    db = SessionLocal()
    summary = {"companies": 0, "boards_found": 0, "new": 0, "total": 0, "no_board": []}
    try:
        targets = (
            db.query(TargetCompany)
            .filter(TargetCompany.status != "Not Interested")
            .all()
        )
        summary["companies"] = len(targets)

        for t in targets:
            found = find_board(t.company_name, t.careers_url or "")
            if not found:
                summary["no_board"].append(t.company_name)
                continue
            source, token, postings = found
            summary["boards_found"] += 1
            summary["total"] += len(postings)
            counts = upsert_postings(db, t.company_name, postings, cv_text)
            summary["new"] += counts["new"]
            log.info("watcher: %s via %s/%s -> %d postings (%d new)",
                     t.company_name, source, token, len(postings), counts["new"])
        return summary
    finally:
        db.close()


# CLI for testing
if __name__ == "__main__":
    result = check_target_companies()
    print(f"Checked {result['companies']} companies, boards found: {result['boards_found']}")
    print(f"Postings: {result['total']} total, {result['new']} new")
    if result["no_board"]:
        print("No board found for:", ", ".join(result["no_board"]))
