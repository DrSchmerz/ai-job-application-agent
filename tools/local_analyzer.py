"""
Local (no-API) job-fit analysis.

Thin wrapper over ``core.matching``, which does boundary-aware skill matching and the
single canonical fit score. This module keeps its historic public API
(``analyze_job_fit_local``, ``extract_keywords``, ``load_cv_summary``, ``tokenize``,
``TECH_KEYWORDS``, ``BUSINESS_KEYWORDS``) so existing imports keep working.
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

from core import matching
from core.matching import (  # re-exported for backwards compatibility
    STOP_WORDS,
    TECH_KEYWORDS,
    BUSINESS_KEYWORDS,
    skill_in_text,
)

PROJECT_ROOT = Path(__file__).parent.parent
CV_SUMMARY_FILE = PROJECT_ROOT / "data" / "cv_summary.txt"


def load_cv_summary() -> str:
    """Load CV summary text (lowercased), or empty string if missing."""
    if CV_SUMMARY_FILE.exists():
        return CV_SUMMARY_FILE.read_text().lower()
    return ""


def tokenize(text: str) -> List[str]:
    """Split text into meaningful lowercase tokens (stop-words removed)."""
    tokens = re.findall(r"[a-z0-9+#]+", (text or "").lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def extract_keywords(text: str) -> Dict[str, List[str]]:
    """Extract technical/business skills (boundary-aware, via core.matching)."""
    skills = matching.extract_skills(text)
    return {"technical": skills["technical"], "business": skills["business"], "other": []}


def analyze_job_fit_local(job_description: str) -> Dict:
    """Analyze job fit using local keyword matching (no API needed)."""
    cv_text = load_cv_summary()
    if not cv_text:
        return {
            "error": "CV summary not found. Please update data/cv_summary.txt",
            "fit_score": 0,
            "recommendation": "Error",
        }
    result = matching.analyze_fit(job_description, cv_text)
    # keep the legacy key that callers expect
    result["jd_keywords"] = extract_keywords(job_description)
    return result


def quick_screen(job_description: str, min_score: int = 5) -> Tuple[bool, Dict]:
    """Quick screen: should you bother applying? Returns (should_apply, analysis)."""
    analysis = analyze_job_fit_local(job_description)
    return analysis.get("fit_score", 0) >= min_score, analysis


if __name__ == "__main__":
    sample_jd = (
        "Solutions Architect with Python, AWS (S3, EC2), data governance, "
        "stakeholder management, Tableau or Power BI, and strong SQL."
    )
    result = analyze_job_fit_local(sample_jd)
    print(f"Fit Score: {result.get('fit_score')}/10 - {result.get('recommendation')}")
    print("Technical matches:", result.get("technical_matches"))
    print("Technical gaps:", result.get("technical_gaps"))
