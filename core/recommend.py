"""
Role / job-title recommendation from a CV.

Given a CV, suggest target roles and the search terms to look for them — the headline
feature for the multi-user direction ("upload your CV, get roles to target"). Uses an LLM
when available, with a deterministic local fallback that scores a small library of roles
by skill overlap so it works offline and is unit-testable.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core import matching
from core.logging_config import get_logger
from core.providers import LLMProvider, parse_json

log = get_logger(__name__)

# Small library of common roles -> indicative skills (used by the local fallback).
ROLE_LIBRARY: Dict[str, List[str]] = {
    "Data Scientist": ["python", "machine learning", "pandas", "scikit-learn", "sql", "analytics"],
    "Machine Learning Engineer": ["python", "pytorch", "tensorflow", "machine learning", "docker", "aws"],
    "Data Engineer": ["python", "sql", "spark", "airflow", "etl", "data pipeline", "aws"],
    "Data Analyst": ["sql", "excel", "tableau", "power bi", "analytics", "business intelligence"],
    "AI / Solutions Engineer": ["llm", "rag", "python", "api", "customer", "presentation"],
    "Data Governance Specialist": ["data governance", "data quality", "metadata", "compliance", "collibra"],
    "Business Analyst": ["requirements", "analysis", "stakeholder", "sql", "communication"],
    "Analytics Consultant": ["consulting", "analytics", "stakeholder", "presentation", "sql", "strategy"],
    "Quantitative Analyst": ["python", "finance", "risk", "sql", "analytics", "machine learning"],
}

_PROMPT = """Given this candidate's CV, suggest the {top_n} best-fit job titles to target.
Respond ONLY with JSON:
{{"recommendations": [
  {{"title": "<job title>", "why": "<one sentence>", "search_terms": ["<term>", "<term>"]}}
]}}

CV:
{cv_text}"""


def _recommend_local(cv_text: str, top_n: int) -> Dict:
    """Score the role library by how many indicative skills appear in the CV."""
    scored = []
    for title, skills in ROLE_LIBRARY.items():
        hits = [s for s in skills if matching.skill_in_text(s, cv_text)]
        if hits:
            scored.append({
                "title": title,
                "why": f"Matches {len(hits)}/{len(skills)} indicative skills: {', '.join(hits[:4])}",
                "search_terms": [title] + hits[:2],
                "_score": len(hits) / len(skills),
            })
    scored.sort(key=lambda r: r["_score"], reverse=True)
    for r in scored:
        r.pop("_score", None)
    return {"recommendations": scored[:top_n], "source": "local"}


def recommend_roles(cv_text: str, llm: Optional[LLMProvider] = None,
                    provider: str = "auto", top_n: int = 5) -> Dict:
    """Recommend target job titles for a CV. LLM when available, else local fallback."""
    cv_text = (cv_text or "").strip()
    if not cv_text:
        return {"recommendations": [], "source": "none"}

    if llm is not None and llm.select(provider) != "local":
        try:
            raw = llm.complete(
                _PROMPT.format(cv_text=cv_text[:8000], top_n=top_n),
                system="You are an expert career advisor.",
                provider=provider,
                json_mode=True,
                temperature=0.4,
            )
            data = parse_json(raw)
            data["source"] = "llm"
            return data
        except Exception as exc:
            log.warning("LLM recommendation failed (%s); using local fallback", exc)

    return _recommend_local(cv_text, top_n)
