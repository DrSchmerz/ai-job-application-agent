"""
Advanced Job Description Analyzer
- Categorizes roles (Sales Engineer vs Solution Architect vs other)
- Extracts key requirements
- Batch analyzes all applications
- Compares with CV for fit scoring
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from db.models import Application
from tools.local_analyzer import (
    load_cv_summary, tokenize, extract_keywords,
    TECH_KEYWORDS, BUSINESS_KEYWORDS
)


# Role category definitions
ROLE_CATEGORIES = {
    "sales_engineer": {
        "keywords": [
            "sales engineer", "se ", "presales", "pre-sales", "technical sales",
            "sales engineering", "demo", "poc", "proof of concept", "rfp", "rfi",
            "customer facing", "quota", "pipeline", "revenue", "deal", "close",
            "technical account", "tam", "customer success engineer"
        ],
        "title_patterns": [
            "sales engineer", "se", "presales", "pre-sales", "technical sales",
            "solutions engineer", "customer engineer"
        ],
        "description": "Technical sales role focused on demos, POCs, and closing deals"
    },
    "solution_architect": {
        "keywords": [
            "solution architect", "solutions architect", "enterprise architect",
            "technical architect", "cloud architect", "data architect",
            "architecture", "design", "blueprint", "implementation", "integration",
            "technical leadership", "best practices", "reference architecture"
        ],
        "title_patterns": [
            "solution architect", "solutions architect", "architect",
            "technical consultant", "implementation"
        ],
        "description": "Technical design role focused on architecture and implementation"
    },
    "consultant": {
        "keywords": [
            "consultant", "consulting", "advisory", "professional services",
            "implementation consultant", "functional consultant", "business consultant",
            "engagement manager", "delivery", "project"
        ],
        "title_patterns": [
            "consultant", "advisory", "engagement manager", "delivery"
        ],
        "description": "Professional services role focused on delivery and consulting"
    },
    "data_role": {
        "keywords": [
            "data engineer", "data scientist", "data analyst", "analytics engineer",
            "ml engineer", "machine learning", "ai engineer", "data governance",
            "bi developer", "etl", "data pipeline"
        ],
        "title_patterns": [
            "data", "analytics", "ml", "machine learning", "ai engineer"
        ],
        "description": "Data-focused technical role"
    }
}

# Seniority levels
SENIORITY_KEYWORDS = {
    "senior": ["senior", "sr.", "sr ", "lead", "principal", "staff", "iii", "3"],
    "mid": ["mid", "ii", "2", "experienced"],
    "junior": ["junior", "jr.", "jr ", "entry", "associate", "i", "1", "graduate"]
}


def categorize_role(title: str, job_description: str) -> Dict:
    """
    Categorize a job into role type based on title and description.

    Returns:
        Dict with category, confidence, and seniority
    """
    title_lower = title.lower() if title else ""
    jd_lower = job_description.lower() if job_description else ""
    combined = f"{title_lower} {jd_lower}"

    scores = {}

    for category, config in ROLE_CATEGORIES.items():
        score = 0

        # Check title patterns (weighted higher)
        for pattern in config["title_patterns"]:
            if pattern in title_lower:
                score += 3

        # Check description keywords
        for keyword in config["keywords"]:
            if keyword in combined:
                score += 1

        scores[category] = score

    # Get best category
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # Determine confidence
    if best_score >= 5:
        confidence = "high"
    elif best_score >= 3:
        confidence = "medium"
    else:
        confidence = "low"
        best_category = "other"

    # Determine seniority
    seniority = "mid"  # default
    for level, keywords in SENIORITY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                seniority = level
                break

    return {
        "category": best_category,
        "confidence": confidence,
        "seniority": seniority,
        "scores": scores,
        "description": ROLE_CATEGORIES.get(best_category, {}).get("description", "Uncategorized role")
    }


def extract_requirements(job_description: str) -> Dict:
    """
    Extract detailed requirements from job description.

    Returns:
        Dict with required_skills, nice_to_have, experience_years, etc.
    """
    jd_lower = job_description.lower() if job_description else ""

    # Extract keywords
    keywords = extract_keywords(job_description)

    # Try to find experience requirements
    import re
    exp_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
        r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:relevant|professional)',
        r'experience:\s*(\d+)\+?\s*years?'
    ]

    experience_years = None
    for pattern in exp_patterns:
        match = re.search(pattern, jd_lower)
        if match:
            experience_years = int(match.group(1))
            break

    # Categorize skills into required vs nice-to-have
    # Simple heuristic: skills mentioned before "nice to have" or "preferred" are required
    required_skills = []
    nice_to_have = []

    nice_to_have_pos = float('inf')
    for marker in ["nice to have", "preferred", "bonus", "plus", "ideally"]:
        pos = jd_lower.find(marker)
        if pos > 0 and pos < nice_to_have_pos:
            nice_to_have_pos = pos

    all_tech = keywords.get('technical', [])

    # Simple split based on position (this is a heuristic)
    for skill in all_tech:
        skill_pos = jd_lower.find(skill.lower())
        if skill_pos < nice_to_have_pos:
            required_skills.append(skill)
        else:
            nice_to_have.append(skill)

    return {
        "required_skills": required_skills,
        "nice_to_have": nice_to_have,
        "business_skills": keywords.get('business', []),
        "experience_years": experience_years,
        "all_keywords": keywords
    }


def analyze_job(application: Application, cv_text: str = None) -> Dict:
    """
    Comprehensive analysis of a single job application.
    """
    if cv_text is None:
        cv_text = load_cv_summary()

    cv_lower = cv_text.lower()

    # Categorize role
    role_info = categorize_role(application.role, application.job_description)

    # Extract requirements
    requirements = extract_requirements(application.job_description or "")

    # Calculate CV match
    required_match = []
    required_gap = []
    for skill in requirements["required_skills"]:
        if skill.lower() in cv_lower:
            required_match.append(skill)
        else:
            required_gap.append(skill)

    nice_match = []
    for skill in requirements["nice_to_have"]:
        if skill.lower() in cv_lower:
            nice_match.append(skill)

    business_match = []
    for skill in requirements["business_skills"]:
        if skill.lower() in cv_lower:
            business_match.append(skill)

    # Calculate fit score
    total_required = len(requirements["required_skills"])
    matched_required = len(required_match)

    if total_required > 0:
        required_score = (matched_required / total_required) * 7  # Max 7 points
    else:
        required_score = 3.5  # Neutral

    nice_score = min(len(nice_match) * 0.5, 2)  # Max 2 points
    business_score = min(len(business_match) * 0.5, 1)  # Max 1 point

    fit_score = round(required_score + nice_score + business_score)
    fit_score = max(1, min(10, fit_score))

    # Recommendation
    if fit_score >= 8:
        recommendation = "Strong Apply"
    elif fit_score >= 6:
        recommendation = "Apply"
    elif fit_score >= 4:
        recommendation = "Consider"
    else:
        recommendation = "Weak Fit"

    return {
        "application_id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status,
        "role_category": role_info["category"],
        "role_confidence": role_info["confidence"],
        "seniority": role_info["seniority"],
        "fit_score": fit_score,
        "recommendation": recommendation,
        "required_skills_matched": required_match,
        "required_skills_gap": required_gap,
        "nice_to_have_matched": nice_match,
        "business_skills_matched": business_match,
        "experience_required": requirements["experience_years"],
        "has_job_description": bool(application.job_description)
    }


def batch_analyze_all() -> Dict:
    """
    Analyze all applications in the database.

    Returns:
        Dict with summary statistics and individual analyses
    """
    db = SessionLocal()
    applications = db.query(Application).all()
    db.close()

    cv_text = load_cv_summary()

    analyses = []
    category_counts = Counter()
    seniority_counts = Counter()
    recommendation_counts = Counter()

    for app in applications:
        if app.job_description and len(app.job_description) > 100:
            analysis = analyze_job(app, cv_text)
            analyses.append(analysis)

            category_counts[analysis["role_category"]] += 1
            seniority_counts[analysis["seniority"]] += 1
            recommendation_counts[analysis["recommendation"]] += 1

    # Sort by fit score
    analyses.sort(key=lambda x: x["fit_score"], reverse=True)

    # Get common skill gaps
    all_gaps = []
    for a in analyses:
        all_gaps.extend(a["required_skills_gap"])
    common_gaps = Counter(all_gaps).most_common(10)

    # Get common matched skills
    all_matches = []
    for a in analyses:
        all_matches.extend(a["required_skills_matched"])
    common_matches = Counter(all_matches).most_common(10)

    return {
        "total_analyzed": len(analyses),
        "by_category": dict(category_counts),
        "by_seniority": dict(seniority_counts),
        "by_recommendation": dict(recommendation_counts),
        "common_skill_gaps": common_gaps,
        "common_skill_matches": common_matches,
        "top_fits": analyses[:5],
        "all_analyses": analyses
    }


def get_roles_by_category(category: str) -> List[Dict]:
    """
    Get all applications of a specific role category.
    """
    result = batch_analyze_all()
    return [a for a in result["all_analyses"] if a["role_category"] == category]


# CLI for testing
if __name__ == "__main__":
    print("🔍 Batch Job Analyzer\n")

    result = batch_analyze_all()

    print(f"📊 Analyzed {result['total_analyzed']} applications with job descriptions\n")

    print("📁 By Role Category:")
    for cat, count in result["by_category"].items():
        print(f"   {cat}: {count}")

    print("\n📈 By Seniority:")
    for sen, count in result["by_seniority"].items():
        print(f"   {sen}: {count}")

    print("\n💡 Recommendations:")
    for rec, count in result["by_recommendation"].items():
        print(f"   {rec}: {count}")

    print("\n⚠️ Top Skill Gaps (skills to learn/highlight):")
    for skill, count in result["common_skill_gaps"][:5]:
        print(f"   - {skill} (missing in {count} jobs)")

    print("\n✅ Your Strongest Matching Skills:")
    for skill, count in result["common_skill_matches"][:5]:
        print(f"   - {skill} (matched in {count} jobs)")

    print("\n🏆 Top 5 Best Fit Applications:")
    for a in result["top_fits"]:
        print(f"   {a['fit_score']}/10 | {a['company']} - {a['role']} ({a['role_category']})")
