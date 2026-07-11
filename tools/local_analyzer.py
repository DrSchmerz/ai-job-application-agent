"""
Local AI Tools - No API Required
Works offline for quick keyword matching and job analysis.
"""
import re
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Set

# Common stop words to filter out
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has',
    'have', 'in', 'is', 'it', 'of', 'on', 'or', 'that', 'the', 'to', 'was',
    'were', 'will', 'with', 'you', 'your', 'we', 'our', 'their', 'this',
    'can', 'do', 'does', 'if', 'may', 'must', 'should', 'would', 'could',
    'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
    'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'just', 'but', 'now', 'also', 'well', 'even',
    'work', 'working', 'team', 'teams', 'role', 'position', 'job', 'company',
    'experience', 'years', 'year', 'looking', 'seeking', 'join', 'opportunity',
    'responsibilities', 'requirements', 'qualifications', 'skills', 'ability',
    'strong', 'excellent', 'good', 'great', 'best', 'ideal', 'preferred',
    'required', 'must', 'should', 'including', 'using', 'used', 'etc'
}

# Technical skills to look for (expanded list)
TECH_KEYWORDS = {
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'sql', 'r', 'scala', 'go',
    'rust', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',

    # Data & ML
    'pandas', 'numpy', 'scikit-learn', 'sklearn', 'tensorflow', 'pytorch',
    'keras', 'xgboost', 'lightgbm', 'machine learning', 'ml', 'deep learning',
    'nlp', 'natural language processing', 'computer vision', 'ai', 'llm',
    'rag', 'langchain', 'hugging face', 'transformers',

    # Data Tools
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'spark', 'hadoop', 'airflow', 'dbt', 'etl', 'data pipeline',
    'tableau', 'power bi', 'looker', 'metabase',

    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'google cloud', 's3', 'ec2', 'lambda',
    'docker', 'kubernetes', 'k8s', 'terraform', 'jenkins', 'ci/cd',
    'git', 'github', 'gitlab',

    # Specific Tools
    'collibra', 'informatica', 'talend', 'snowflake', 'databricks',
    'sas', 'spss', 'stata', 'excel', 'vba',
    'streamlit', 'flask', 'django', 'fastapi', 'rest api', 'api',

    # Concepts
    'data governance', 'data management', 'data quality', 'metadata',
    'data architecture', 'data modeling', 'data warehouse', 'data lake',
    'analytics', 'business intelligence', 'bi', 'reporting',
    'agile', 'scrum', 'jira', 'confluence'
}

# Business/Soft skills
BUSINESS_KEYWORDS = {
    'stakeholder', 'stakeholders', 'communication', 'presentation',
    'leadership', 'management', 'consulting', 'client', 'customer',
    'requirements', 'analysis', 'problem solving', 'critical thinking',
    'collaboration', 'cross-functional', 'project management',
    'strategic', 'strategy', 'planning', 'execution',
    'financial', 'banking', 'finance', 'compliance', 'regulatory',
    'governance', 'risk', 'audit'
}

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CV_SUMMARY_FILE = PROJECT_ROOT / "data" / "cv_summary.txt"


def load_cv_summary() -> str:
    """Load CV summary text."""
    if CV_SUMMARY_FILE.exists():
        return CV_SUMMARY_FILE.read_text().lower()
    return ""


def tokenize(text: str) -> List[str]:
    """Split text into lowercase tokens."""
    # Convert to lowercase and split on non-alphanumeric
    tokens = re.findall(r'[a-z0-9+#]+', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def extract_keywords(text: str) -> Dict[str, List[str]]:
    """
    Extract keywords from text, categorized by type.

    Returns:
        Dict with 'technical', 'business', and 'other' keyword lists
    """
    text_lower = text.lower()
    tokens = set(tokenize(text))

    # Find multi-word phrases
    found_tech = []
    found_business = []

    # Check for technical keywords (including multi-word)
    for keyword in TECH_KEYWORDS:
        if keyword in text_lower:
            found_tech.append(keyword)

    # Check for business keywords
    for keyword in BUSINESS_KEYWORDS:
        if keyword in text_lower:
            found_business.append(keyword)

    # Other significant words (nouns, likely important)
    other_words = [t for t in tokens
                   if t not in STOP_WORDS
                   and t not in ''.join(found_tech).split()
                   and t not in ''.join(found_business).split()
                   and len(t) > 3]

    # Count frequency
    word_counts = Counter(tokenize(text))
    other_sorted = sorted(other_words, key=lambda x: word_counts.get(x, 0), reverse=True)

    return {
        'technical': list(set(found_tech)),
        'business': list(set(found_business)),
        'other': other_sorted[:20]  # Top 20 other keywords
    }


def match_keywords(jd_keywords: Dict[str, List[str]], cv_text: str) -> Dict[str, any]:
    """
    Match job description keywords against CV.

    Returns:
        Dict with matches, gaps, and scores
    """
    cv_lower = cv_text.lower()

    results = {
        'technical': {'matched': [], 'missing': []},
        'business': {'matched': [], 'missing': []},
        'other': {'matched': [], 'missing': []}
    }

    for category, keywords in jd_keywords.items():
        for kw in keywords:
            if kw in cv_lower:
                results[category]['matched'].append(kw)
            else:
                results[category]['missing'].append(kw)

    return results


def calculate_fit_score(match_results: Dict) -> Tuple[int, str]:
    """
    Calculate overall fit score (1-10) based on keyword matches.

    Returns:
        Tuple of (score, recommendation)
    """
    tech_matched = len(match_results['technical']['matched'])
    tech_total = tech_matched + len(match_results['technical']['missing'])

    biz_matched = len(match_results['business']['matched'])
    biz_total = biz_matched + len(match_results['business']['missing'])

    # Weighted scoring: technical skills matter more
    if tech_total > 0:
        tech_score = (tech_matched / tech_total) * 6  # Max 6 points
    else:
        tech_score = 3  # Neutral if no tech requirements

    if biz_total > 0:
        biz_score = (biz_matched / biz_total) * 4  # Max 4 points
    else:
        biz_score = 2  # Neutral if no business requirements

    total_score = round(tech_score + biz_score)
    total_score = max(1, min(10, total_score))  # Clamp to 1-10

    # Recommendation
    if total_score >= 8:
        recommendation = "Strong Apply"
    elif total_score >= 6:
        recommendation = "Apply"
    elif total_score >= 4:
        recommendation = "Consider"
    else:
        recommendation = "Weak Fit"

    return total_score, recommendation


def analyze_job_fit_local(job_description: str) -> Dict:
    """
    Analyze job fit using local keyword matching (no API needed).

    Args:
        job_description: Full job description text

    Returns:
        Dict with analysis results
    """
    # Load CV
    cv_text = load_cv_summary()

    if not cv_text:
        return {
            'error': 'CV summary not found. Please update data/cv_summary.txt',
            'fit_score': 0,
            'recommendation': 'Error'
        }

    # Extract keywords from JD
    jd_keywords = extract_keywords(job_description)

    # Match against CV
    matches = match_keywords(jd_keywords, cv_text)

    # Calculate score
    score, recommendation = calculate_fit_score(matches)

    return {
        'fit_score': score,
        'recommendation': recommendation,
        'technical_matches': matches['technical']['matched'],
        'technical_gaps': matches['technical']['missing'],
        'business_matches': matches['business']['matched'],
        'business_gaps': matches['business']['missing'],
        'jd_keywords': jd_keywords,
        'analysis_type': 'local'  # Indicates this was local analysis
    }


def quick_screen(job_description: str, min_score: int = 5) -> Tuple[bool, Dict]:
    """
    Quick screening to decide if worth applying.

    Args:
        job_description: Job description text
        min_score: Minimum score to pass screening (default 5)

    Returns:
        Tuple of (should_apply: bool, analysis: dict)
    """
    analysis = analyze_job_fit_local(job_description)
    should_apply = analysis.get('fit_score', 0) >= min_score
    return should_apply, analysis


def batch_screen_urls(urls: List[str], min_score: int = 5) -> List[Dict]:
    """
    Screen multiple job URLs (placeholder - needs web scraping).
    For now, returns structure for future implementation.
    """
    # TODO: Implement web scraping
    return [{'url': url, 'status': 'not_implemented'} for url in urls]


# CLI for testing
if __name__ == "__main__":
    print("🔍 Local Job Analyzer - No API Required\n")

    # Test with sample JD
    sample_jd = """
    We are looking for a Solutions Architect with experience in:
    - Python programming and data analysis
    - AWS cloud services (S3, EC2)
    - Data governance and compliance
    - Stakeholder management and presentations
    - Financial services industry experience preferred
    - Experience with Tableau or Power BI
    - Strong SQL skills
    """

    print("📋 Sample Job Description:")
    print(sample_jd)
    print("\n" + "="*50 + "\n")

    result = analyze_job_fit_local(sample_jd)

    print(f"📊 Fit Score: {result['fit_score']}/10")
    print(f"💡 Recommendation: {result['recommendation']}")

    print(f"\n✅ Technical Matches ({len(result['technical_matches'])}):")
    for match in result['technical_matches']:
        print(f"   • {match}")

    print(f"\n❌ Technical Gaps ({len(result['technical_gaps'])}):")
    for gap in result['technical_gaps']:
        print(f"   • {gap}")

    print(f"\n✅ Business Matches ({len(result['business_matches'])}):")
    for match in result['business_matches']:
        print(f"   • {match}")

    print(f"\n❌ Business Gaps ({len(result['business_gaps'])}):")
    for gap in result['business_gaps']:
        print(f"   • {gap}")
