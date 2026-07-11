"""
MCP Server for the Job Application Agent.

Exposes 15 tools for Claude Code to use:
- Agent Tools (5): analyze_job_fit, generate_cover_letter, process_full_application,
                   answer_application_question, prepare_for_interview
- Data Tools (8): list_applications, get_application, add_application, get_application_stats,
                  list_cover_letters, update_application_status, add_interview_note, get_application_timeline
- Analysis Tools (2): quick_screen, categorize_role
"""
import sys
from pathlib import Path
from typing import Optional, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Initialize database
from db.session import init_db
init_db()

# Import FastMCP
from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("job-application-agent")


# =============================================================================
# AGENT TOOLS (AI-powered)
# =============================================================================

@mcp.tool()
def analyze_job_fit(
    job_description: str,
    use_cloud: bool = True
) -> dict:
    """
    Analyze how well the candidate fits a job based on the description.

    Args:
        job_description: The full job description text to analyze
        use_cloud: If True, use cloud AI provider for deeper analysis; if False, use fast local keyword matching

    Returns:
        Analysis with fit_score (1-10), strengths, gaps, recommendation, and reasoning
    """
    from mcp_server.tools.agent_tools import analyze_job_fit as _analyze
    return _analyze(job_description, use_cloud)


@mcp.tool()
def generate_cover_letter(
    company: str,
    role: str,
    job_description: str,
    provider: Optional[str] = None
) -> dict:
    """
    Generate a tailored cover letter for a specific job application.

    Args:
        company: The company name
        role: The job title/role
        job_description: The full job description text
        provider: Optional LLM provider override (groq, google, openai). If not specified, uses best available.

    Returns:
        Generated cover letter text with metadata
    """
    from mcp_server.tools.agent_tools import generate_cover_letter as _generate
    return _generate(company, role, job_description, provider)


@mcp.tool()
def process_full_application(
    company: str,
    role: str,
    job_description: str,
    job_url: Optional[str] = None,
    generate_cover_letter: bool = True,
    generate_cv_tips: bool = True,
    provider: Optional[str] = None
) -> dict:
    """
    Complete application workflow: analyze job fit, generate cover letter, and get CV customization tips.

    This is the most comprehensive tool - it runs the full analysis pipeline.

    Args:
        company: The company name
        role: The job title/role
        job_description: The full job description text
        job_url: Optional URL to the job posting
        generate_cover_letter: Whether to generate a tailored cover letter (default: True)
        generate_cv_tips: Whether to generate CV customization suggestions (default: True)
        provider: Optional LLM provider override (groq, google, openai)

    Returns:
        Complete analysis with fit_score, role categorization, cover letter, and CV tips
    """
    from mcp_server.tools.agent_tools import process_full_application as _process
    return _process(
        company, role, job_description, job_url,
        generate_cover_letter, generate_cv_tips, provider
    )


@mcp.tool()
def answer_application_question(
    question: str,
    company: str,
    role: str,
    job_description: str,
    max_words: int = 200,
    tone: str = "professional",
    provider: Optional[str] = None
) -> dict:
    """
    Generate an answer to an application form question.

    Uses your CV and the job context to craft a tailored response.
    Great for questions like "Why do you want to work here?" or "Describe a challenge you overcame."

    Args:
        question: The question from the application form
        company: The company name
        role: The job title/role
        job_description: The job description for context
        max_words: Maximum words for the answer (default: 200)
        tone: Tone of the answer - "professional", "enthusiastic", "concise" (default: professional)
        provider: Optional LLM provider override

    Returns:
        Generated answer with word count and metadata
    """
    from mcp_server.tools.agent_tools import answer_application_question as _answer
    return _answer(question, company, role, job_description, max_words, tone, provider)


@mcp.tool()
def prepare_for_interview(
    application_id: int,
    interview_type: str = "general",
    focus_areas: Optional[List[str]] = None,
    provider: Optional[str] = None
) -> dict:
    """
    Generate interview preparation materials for a tracked application.

    Creates customized prep based on the job description, your CV, and any previous interview notes.

    Args:
        application_id: The database ID of the application to prepare for
        interview_type: Type of interview - "general", "technical", "behavioral", "final" (default: general)
        focus_areas: Optional list of specific areas to focus on (e.g., ["system design", "leadership"])
        provider: Optional LLM provider override

    Returns:
        Interview prep with likely questions, talking points, questions to ask, and tips
    """
    from mcp_server.tools.agent_tools import prepare_for_interview as _prepare
    return _prepare(application_id, interview_type, focus_areas, provider)


# =============================================================================
# DATA TOOLS (Database operations)
# =============================================================================

@mcp.tool()
def list_applications(
    status: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    List job applications from the database with optional filters.

    Args:
        status: Filter by status (e.g., "Applied", "Interview", "Rejected", "Draft", "Offer")
        company: Filter by company name (partial match, case-insensitive)
        limit: Maximum number of results (default: 50)

    Returns:
        List of applications with summary information
    """
    from mcp_server.tools.data_tools import list_applications as _list
    return _list(status, company, limit)


@mcp.tool()
def get_application(application_id: int) -> dict:
    """
    Get full details of a single application by its ID.

    Args:
        application_id: The database ID of the application

    Returns:
        Complete application details including job description, cover letter, and analysis
    """
    from mcp_server.tools.data_tools import get_application as _get
    return _get(application_id)


@mcp.tool()
def add_application(
    company: str,
    role: str,
    job_description: Optional[str] = None,
    job_url: Optional[str] = None,
    status: str = "Draft",
    notes: Optional[str] = None,
    fit_score: Optional[float] = None,
    role_category: Optional[str] = None,
    seniority_level: Optional[str] = None,
    cover_letter_text: Optional[str] = None,
    cv_suggestions: Optional[str] = None
) -> dict:
    """
    Add a new job application to the tracking database.

    Args:
        company: Company name (required)
        role: Job title/role (required)
        job_description: Full job description text
        job_url: URL to the job posting
        status: Application status (default: "Draft"). Options: Draft, Applied, Interview, Rejected, Offer, Accepted
        notes: Additional notes about the application
        fit_score: Pre-calculated fit score (1-10)
        role_category: Role type (sales_engineer, solution_architect, consultant, data_role, other)
        seniority_level: Seniority level (junior, mid, senior)
        cover_letter_text: Generated cover letter content
        cv_suggestions: CV customization suggestions

    Returns:
        Created application summary
    """
    from mcp_server.tools.data_tools import add_application as _add
    return _add(
        company, role, job_description, job_url, status, notes,
        fit_score, role_category, seniority_level, cover_letter_text, cv_suggestions
    )


@mcp.tool()
def get_application_stats() -> dict:
    """
    Get summary statistics about all tracked applications.

    Returns:
        Total count and breakdown by status (applied, interview, rejected, offer, accepted)
    """
    from mcp_server.tools.data_tools import get_application_stats as _stats
    return _stats()


@mcp.tool()
def list_cover_letters() -> dict:
    """
    List all saved cover letter files from the cover_letters directory.

    Returns:
        List of cover letter files with their associated companies
    """
    from mcp_server.tools.data_tools import list_cover_letters as _list_letters
    return _list_letters()


@mcp.tool()
def update_application_status(
    application_id: int,
    status: str,
    notes: Optional[str] = None
) -> dict:
    """
    Update the status of an application and optionally add notes.

    Use this to track progress through the interview pipeline.

    Args:
        application_id: The database ID of the application
        status: New status. Options:
            - "Draft" - Initial state, not yet applied
            - "Applied" - Application submitted
            - "Phone Screen" - Phone/video screening scheduled or completed
            - "Technical Interview" - Technical round
            - "Final Round" - Final interviews
            - "Offer" - Received offer
            - "Accepted" - Accepted offer
            - "Rejected" - Application rejected
            - "Withdrawn" - You withdrew from consideration
        notes: Optional notes about this status change (e.g., "Scheduled for Feb 10 at 2pm")

    Returns:
        Updated application summary with previous status
    """
    from mcp_server.tools.data_tools import update_application_status as _update
    return _update(application_id, status, notes)


@mcp.tool()
def add_interview_note(
    application_id: int,
    note: str,
    interview_type: Optional[str] = None,
    interviewer: Optional[str] = None,
    questions_asked: Optional[List[str]] = None
) -> dict:
    """
    Add an interview note or comment to an application.

    Use this to track interview feedback, questions asked, impressions, and learnings.

    Args:
        application_id: The database ID of the application
        note: The note content (required) - your impressions, feedback, what went well/poorly
        interview_type: Type of interview (e.g., "Phone Screen", "Technical", "Behavioral", "Hiring Manager")
        interviewer: Name or role of interviewer if known (e.g., "Sarah - Engineering Manager")
        questions_asked: List of questions that were asked (saved for future interview prep)

    Returns:
        Confirmation with the formatted note that was added
    """
    from mcp_server.tools.data_tools import add_interview_note as _add_note
    return _add_note(application_id, note, interview_type, interviewer, questions_asked)


@mcp.tool()
def get_application_timeline(application_id: int) -> dict:
    """
    Get the full timeline and history of an application.

    Shows all status changes, notes added, when cover letters were generated, etc.
    Useful for reviewing your journey with a specific application.

    Args:
        application_id: The database ID of the application

    Returns:
        Application summary with all notes and chronological history of events
    """
    from mcp_server.tools.data_tools import get_application_timeline as _timeline
    return _timeline(application_id)


# =============================================================================
# ANALYSIS TOOLS (Local, no API required)
# =============================================================================

@mcp.tool()
def quick_screen(
    job_description: str,
    min_score: int = 5
) -> dict:
    """
    Fast local screening to decide if a job is worth applying to.

    Uses keyword matching against the CV - no API calls, instant results.
    This is the fastest way to check job fit.

    Args:
        job_description: The job description text to analyze
        min_score: Minimum score (1-10) to pass screening (default: 5)

    Returns:
        Screening result with should_apply boolean, fit_score, and keyword matches
    """
    from mcp_server.tools.analysis_tools import quick_screen as _screen
    return _screen(job_description, min_score)


@mcp.tool()
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
        job_description: Optional job description for better classification accuracy

    Returns:
        Role classification with category, confidence level, seniority, and description
    """
    from mcp_server.tools.analysis_tools import categorize_role as _categorize
    return _categorize(title, job_description)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    mcp.run()
