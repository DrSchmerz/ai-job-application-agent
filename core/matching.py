"""
Skill extraction, matching, and job-fit scoring.

This module fixes the long-standing correctness bug where skills were matched with
naive substring checks (``"ai" in text``), which made short tokens like ``r``, ``go``,
``ai``, ``ml``, ``bi`` match *inside* unrelated words ("em**ai**l", "**go**od",
"**r**equire"). Matching here is **word/phrase boundary aware**, so a skill only counts
when it appears as a real token or phrase.

It is the single source of truth for fit scoring (previously duplicated and inconsistent
between ``tools/local_analyzer.py`` and ``tools/job_analyzer.py``).
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

# --- Vocabularies -----------------------------------------------------------------

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "were", "will",
    "with", "you", "your", "we", "our", "their", "this", "can", "do", "does", "if",
    "may", "must", "should", "would", "could", "about", "into", "then", "there",
    "when", "where", "why", "how", "all", "each", "more", "most", "other", "some",
    "such", "no", "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "but", "now", "also", "well", "even", "work", "team", "role", "position", "job",
    "company", "experience", "years", "year", "skills", "ability", "strong",
    "required", "including", "using", "etc",
}

TECH_KEYWORDS = {
    # Languages
    "python", "java", "javascript", "typescript", "sql", "r", "scala", "go", "rust",
    "c++", "c#", "ruby", "php", "swift", "kotlin",
    # Data & ML
    "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
    "xgboost", "lightgbm", "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision", "llm", "rag", "langchain",
    "hugging face", "transformers",
    # Data tools
    "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "spark", "hadoop",
    "airflow", "dbt", "etl", "data pipeline", "tableau", "power bi", "looker",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "jenkins", "ci/cd", "git", "github", "gitlab",
    # Specific tools
    "collibra", "informatica", "talend", "snowflake", "databricks", "sas", "spss",
    "excel", "vba", "streamlit", "flask", "django", "fastapi", "rest api",
    # Concepts
    "data governance", "data management", "data quality", "metadata",
    "data architecture", "data modeling", "data warehouse", "data lake", "analytics",
    "business intelligence", "agile", "scrum", "jira", "confluence",
}

BUSINESS_KEYWORDS = {
    "stakeholder", "communication", "presentation", "leadership", "management",
    "consulting", "client", "customer", "requirements", "analysis", "problem solving",
    "critical thinking", "collaboration", "cross-functional", "project management",
    "strategic", "strategy", "planning", "execution", "financial", "banking",
    "finance", "compliance", "regulatory", "governance", "risk", "audit",
}


# --- Boundary-aware matching ------------------------------------------------------

def skill_in_text(skill: str, text: str) -> bool:
    """Return True only if *skill* appears in *text* as a whole token/phrase.

    Unlike ``skill in text``, this does not match inside larger words:
    ``skill_in_text("ai", "email")`` is False, ``skill_in_text("ai", "AI Engineer")``
    is True. Handles symbol-bearing skills like ``c++`` and ``ci/cd``.
    """
    skill = skill.strip().lower()
    if not skill:
        return False
    # A boundary is anything that is not a letter/digit (so "c++", "c#", "ci/cd" work).
    pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def extract_skills(text: str) -> Dict[str, List[str]]:
    """Extract known technical and business skills present in *text* (boundary-aware)."""
    text_l = (text or "").lower()
    technical = sorted({kw for kw in TECH_KEYWORDS if skill_in_text(kw, text_l)})
    business = sorted({kw for kw in BUSINESS_KEYWORDS if skill_in_text(kw, text_l)})
    return {"technical": technical, "business": business}


def match_skills(job_description: str, cv_text: str) -> Dict[str, Dict[str, List[str]]]:
    """Match the skills required by a job description against a CV.

    Returns ``{"technical": {"matched": [...], "missing": [...]}, "business": {...}}``.
    """
    jd_skills = extract_skills(job_description)
    cv_l = (cv_text or "").lower()
    result: Dict[str, Dict[str, List[str]]] = {}
    for category, skills in jd_skills.items():
        matched, missing = [], []
        for skill in skills:
            (matched if skill_in_text(skill, cv_l) else missing).append(skill)
        result[category] = {"matched": matched, "missing": missing}
    return result


# --- Unified fit scoring ----------------------------------------------------------

def compute_fit_score(match: Dict[str, Dict[str, List[str]]]) -> Tuple[int, str]:
    """Single, canonical fit score (1-10) + recommendation from matched skills.

    Technical coverage is weighted more heavily (0-6) than business coverage (0-4).
    When a category has no required skills, it scores a neutral half.
    """
    def coverage(cat: str, weight: float, neutral: float) -> float:
        matched = len(match[cat]["matched"])
        total = matched + len(match[cat]["missing"])
        return (matched / total) * weight if total else neutral

    score = coverage("technical", 6, 3) + coverage("business", 4, 2)
    score = max(1, min(10, round(score)))

    if score >= 8:
        rec = "Strong Apply"
    elif score >= 6:
        rec = "Apply"
    elif score >= 4:
        rec = "Consider"
    else:
        rec = "Weak Fit"
    return score, rec


def analyze_fit(job_description: str, cv_text: str) -> Dict:
    """End-to-end local fit analysis (no API required)."""
    if not cv_text:
        return {"error": "No CV provided", "fit_score": 0, "recommendation": "Error"}

    match = match_skills(job_description, cv_text)
    score, rec = compute_fit_score(match)
    return {
        "fit_score": score,
        "recommendation": rec,
        "technical_matches": match["technical"]["matched"],
        "technical_gaps": match["technical"]["missing"],
        "business_matches": match["business"]["matched"],
        "business_gaps": match["business"]["missing"],
        "analysis_type": "local",
    }
