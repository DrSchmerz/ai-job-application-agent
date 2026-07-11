"""
AI-powered MCP tools that wrap the ApplicationAgent.

These tools use LLM providers (Groq, Google, OpenAI) for:
- Job fit analysis
- Cover letter generation
- Full application processing
"""
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Lazy-load agent to avoid initialization on import
_agent = None


def get_agent():
    """Get or create the ApplicationAgent instance."""
    global _agent
    if _agent is None:
        from agent.agent import ApplicationAgent
        _agent = ApplicationAgent(provider="auto")
    return _agent


def analyze_job_fit(
    job_description: str,
    use_cloud: bool = True
) -> dict:
    """
    Analyze how well the candidate fits a job based on the description.

    Args:
        job_description: The full job description text to analyze
        use_cloud: If True, use cloud AI provider; if False, use fast local keyword matching

    Returns:
        Dict with fit_score (1-10), strengths, gaps, recommendation, and reasoning
    """
    agent = get_agent()
    result = agent.analyze_job_fit(job_description, force_local=not use_cloud)

    return {
        "fit_score": result.get("fit_score", 0),
        "recommendation": result.get("recommendation", "Unknown"),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "reasoning": result.get("reasoning", ""),
        "analysis_type": result.get("analysis_type", "unknown"),
    }


def generate_cover_letter(
    company: str,
    role: str,
    job_description: str,
    provider: Optional[str] = None
) -> dict:
    """
    Generate a tailored cover letter for a specific job.

    Args:
        company: The company name
        role: The job title/role
        job_description: The full job description text
        provider: Optional LLM provider override (groq, google, openai)

    Returns:
        Dict with cover_letter text, provider used, and status
    """
    agent = get_agent()

    try:
        cover_letter = agent.generate_cover_letter(
            company=company,
            role=role,
            job_description=job_description,
            provider=provider
        )

        return {
            "success": True,
            "cover_letter": cover_letter,
            "provider": provider or agent.active_provider,
            "company": company,
            "role": role,
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "provider": provider or agent.active_provider,
            "hint": "Cover letter generation requires a cloud provider (Groq or Google). Check your API keys in .env",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": provider or agent.active_provider,
        }


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
    Complete application workflow: analyze job fit, generate cover letter, and get CV tips.

    Args:
        company: The company name
        role: The job title/role
        job_description: The full job description text
        job_url: Optional URL to the job posting
        generate_cover_letter: Whether to generate a cover letter
        generate_cv_tips: Whether to generate CV customization tips
        provider: Optional LLM provider override (groq, google, openai)

    Returns:
        Dict with fit_analysis, cover_letter, cv_suggestions, and role categorization
    """
    agent = get_agent()

    result = agent.process_full_application(
        company=company,
        role=role,
        job_description=job_description,
        job_url=job_url,
        generate_cover_letter=generate_cover_letter,
        generate_cv_tips=generate_cv_tips,
        provider=provider
    )

    # Clean up the result for JSON serialization
    return {
        "company": result.get("company"),
        "role": result.get("role"),
        "job_url": result.get("job_url"),
        "fit_score": result.get("fit_score"),
        "fit_analysis": result.get("fit_analysis"),
        "role_category": result.get("role_category"),
        "seniority_level": result.get("seniority_level"),
        "cover_letter": result.get("cover_letter"),
        "cover_letter_error": result.get("cover_letter_error"),
        "cv_suggestions": result.get("cv_suggestions"),
        "provider": provider or agent.active_provider,
    }


def get_agent_status() -> dict:
    """
    Get the current status of the ApplicationAgent.

    Returns:
        Dict with active_provider, available_providers, and cv_loaded status
    """
    agent = get_agent()
    return agent.get_status()


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

    Args:
        question: The question from the application form (e.g., "Why do you want to work here?")
        company: The company name
        role: The job title/role
        job_description: The job description for context
        max_words: Maximum words for the answer (default: 200)
        tone: Tone of the answer - "professional", "enthusiastic", "concise" (default: professional)
        provider: Optional LLM provider override

    Returns:
        Generated answer with metadata
    """
    agent = get_agent()
    use_provider = provider or agent.active_provider

    if use_provider == "local":
        return {
            "success": False,
            "error": "Answering questions requires a cloud provider. Check your API keys.",
        }

    prompt = f"""You are helping a job applicant answer an application question.
Write a compelling, honest answer based on their background.

CANDIDATE BACKGROUND:
{agent.cv_summary}

TARGET ROLE: {role} at {company}

JOB DESCRIPTION:
{job_description}

APPLICATION QUESTION:
{question}

INSTRUCTIONS:
- Write in first person as the candidate
- Keep the answer under {max_words} words
- Tone: {tone}
- Be specific and reference relevant experience from the CV
- Connect your background to what the company is looking for
- Be authentic - don't make up experience

Answer:"""

    try:
        if use_provider == "groq":
            response = agent._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a professional career advisor helping craft application answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            answer = response.choices[0].message.content.strip()
        elif use_provider == "google":
            response = agent._google_model.generate_content(prompt)
            answer = response.text.strip()
        elif use_provider == "openai":
            response = agent._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional career advisor helping craft application answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            answer = response.choices[0].message.content.strip()
        else:
            return {"success": False, "error": f"Unknown provider: {use_provider}"}

        # Count words
        word_count = len(answer.split())

        return {
            "success": True,
            "question": question,
            "answer": answer,
            "word_count": word_count,
            "company": company,
            "role": role,
            "provider": use_provider,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": use_provider,
        }


def prepare_for_interview(
    application_id: int,
    interview_type: str = "general",
    focus_areas: Optional[list] = None,
    provider: Optional[str] = None
) -> dict:
    """
    Generate interview preparation materials based on a tracked application.

    Args:
        application_id: The database ID of the application to prepare for
        interview_type: Type of interview - "general", "technical", "behavioral", "final"
        focus_areas: Optional list of specific areas to focus on (e.g., ["system design", "leadership"])
        provider: Optional LLM provider override

    Returns:
        Interview prep with likely questions, talking points, and company research tips
    """
    # Get application details
    from db.session import SessionLocal
    from tools.data_tools import get_application_by_id

    db = SessionLocal()
    try:
        app = get_application_by_id(application_id, db=db)
        if app is None:
            return {
                "success": False,
                "error": f"Application with ID {application_id} not found",
            }

        if not app.job_description:
            return {
                "success": False,
                "error": "No job description saved for this application. Add the JD first.",
            }

        agent = get_agent()
        use_provider = provider or agent.active_provider

        if use_provider == "local":
            return {
                "success": False,
                "error": "Interview prep requires a cloud provider. Check your API keys.",
            }

        focus_text = ""
        if focus_areas:
            focus_text = f"\nFOCUS AREAS: {', '.join(focus_areas)}"

        # Include previous interview notes if available
        notes_context = ""
        if app.notes:
            notes_context = f"\nPREVIOUS INTERVIEW NOTES:\n{app.notes}"

        prompt = f"""You are a career coach preparing a candidate for a job interview.

CANDIDATE BACKGROUND:
{agent.cv_summary}

COMPANY: {app.company}
ROLE: {app.role}
INTERVIEW TYPE: {interview_type}
{focus_text}

JOB DESCRIPTION:
{app.job_description}
{notes_context}

Generate comprehensive interview preparation including:

1. **LIKELY QUESTIONS** (5-7 questions they might ask based on the JD)
   - Include the question and a suggested talking point from the candidate's background

2. **YOUR QUESTIONS TO ASK** (3-4 thoughtful questions to ask the interviewer)

3. **KEY POINTS TO EMPHASIZE** (4-5 experiences/skills from CV that align with this role)

4. **POTENTIAL CONCERNS TO ADDRESS** (Any gaps or concerns and how to handle them)

5. **COMPANY RESEARCH TIPS** (What to research about {app.company} before the interview)

Be specific to this role and candidate's actual background."""

        try:
            if use_provider == "groq":
                response = agent._groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert interview coach."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                prep = response.choices[0].message.content.strip()
            elif use_provider == "google":
                response = agent._google_model.generate_content(prompt)
                prep = response.text.strip()
            elif use_provider == "openai":
                response = agent._openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert interview coach."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                prep = response.choices[0].message.content.strip()
            else:
                return {"success": False, "error": f"Unknown provider: {use_provider}"}

            return {
                "success": True,
                "company": app.company,
                "role": app.role,
                "interview_type": interview_type,
                "preparation": prep,
                "fit_score": app.fit_score,
                "provider": use_provider,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": use_provider,
            }
    finally:
        db.close()
