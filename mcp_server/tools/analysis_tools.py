"""
Local analysis MCP tools that don't require API calls.

These tools provide fast, offline analysis using keyword matching:
- Quick screening (pass/fail)
- Role categorization
- Keyword extraction
"""
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def quick_screen(
    job_description: str,
    min_score: int = 5
) -> dict:
    """
    Fast local screening to decide if a job is worth applying to.

    Uses keyword matching against CV - no API calls, instant results.

    Args:
        job_description: The job description text to analyze
        min_score: Minimum score (1-10) to pass screening (default: 5)

    Returns:
        Dict with should_apply boolean, fit_score, recommendation, and keyword matches
    """
    from tools.local_analyzer import quick_screen as _quick_screen

    should_apply, analysis = _quick_screen(job_description, min_score=min_score)

    return {
        "should_apply": should_apply,
        "fit_score": analysis.get("fit_score", 0),
        "recommendation": analysis.get("recommendation", "Unknown"),
        "min_score_threshold": min_score,
        "technical_matches": analysis.get("technical_matches", []),
        "technical_gaps": analysis.get("technical_gaps", []),
        "business_matches": analysis.get("business_matches", []),
        "business_gaps": analysis.get("business_gaps", []),
        "analysis_type": "local_keyword_matching",
    }


def categorize_role(
    title: str,
    job_description: str = ""
) -> dict:
    """
    Classify a job role into category and seniority level.

    Categories: sales_engineer, solution_architect, consultant, data_role, other
    Seniority: junior, mid, senior

    Args:
        title: The job title
        job_description: Optional job description for better classification

    Returns:
        Dict with category, confidence, seniority, and category description
    """
    from tools.job_analyzer import categorize_role as _categorize_role

    result = _categorize_role(title, job_description)

    return {
        "category": result.get("category", "other"),
        "confidence": result.get("confidence", "low"),
        "seniority": result.get("seniority", "mid"),
        "description": result.get("description", ""),
        "category_scores": result.get("scores", {}),
    }


def extract_job_requirements(job_description: str) -> dict:
    """
    Extract structured requirements from a job description.

    Args:
        job_description: The full job description text

    Returns:
        Dict with required_skills, nice_to_have, business_skills, and experience_years
    """
    from tools.job_analyzer import extract_requirements

    result = extract_requirements(job_description)

    return {
        "required_skills": result.get("required_skills", []),
        "nice_to_have": result.get("nice_to_have", []),
        "business_skills": result.get("business_skills", []),
        "experience_years": result.get("experience_years"),
        "all_keywords": result.get("all_keywords", {}),
    }


def extract_keywords(text: str) -> dict:
    """
    Extract and categorize keywords from any text.

    Args:
        text: Text to analyze (job description, CV, etc.)

    Returns:
        Dict with technical, business, and other keywords found
    """
    from tools.local_analyzer import extract_keywords as _extract_keywords

    result = _extract_keywords(text)

    return {
        "technical": result.get("technical", []),
        "business": result.get("business", []),
        "other": result.get("other", []),
        "total_count": (
            len(result.get("technical", [])) +
            len(result.get("business", [])) +
            len(result.get("other", []))
        ),
    }


def batch_analyze_applications() -> dict:
    """
    Analyze all applications in the database at once.

    Provides insights across all tracked applications including:
    - Distribution by role category and seniority
    - Common skill gaps and matches
    - Top fitting jobs

    Returns:
        Dict with summary statistics and top fits
    """
    from tools.job_analyzer import batch_analyze_all

    result = batch_analyze_all()

    # Simplify the top_fits to avoid massive output
    top_fits = []
    for fit in result.get("top_fits", [])[:5]:
        top_fits.append({
            "id": fit.get("application_id"),
            "company": fit.get("company"),
            "role": fit.get("role"),
            "fit_score": fit.get("fit_score"),
            "recommendation": fit.get("recommendation"),
            "category": fit.get("role_category"),
        })

    return {
        "total_analyzed": result.get("total_analyzed", 0),
        "by_category": result.get("by_category", {}),
        "by_seniority": result.get("by_seniority", {}),
        "by_recommendation": result.get("by_recommendation", {}),
        "common_skill_gaps": result.get("common_skill_gaps", [])[:10],
        "common_skill_matches": result.get("common_skill_matches", [])[:10],
        "top_fits": top_fits,
    }
