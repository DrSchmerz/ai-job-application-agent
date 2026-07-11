"""
Multi-Provider AI Agent for generating tailored cover letters.
Supports: Local (keyword matching), Groq, Google Gemini, OpenAI
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional, Literal

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
CV_SUMMARY_FILE = PROJECT_ROOT / "data" / "cv_summary.txt"

# Add project root to path for imports
sys.path.insert(0, str(PROJECT_ROOT))

# Provider type
ProviderType = Literal["local", "groq", "google", "openai", "auto"]


class ApplicationAgent:
    """
    Multi-provider AI Agent for job application assistance.

    Providers:
    - local: Keyword matching (free, offline)
    - groq: Groq API with Llama models (free tier)
    - google: Google Gemini API (free tier)
    - openai: OpenAI API (paid)
    - auto: Try providers in order until one works
    """

    def __init__(self, provider: ProviderType = "auto"):
        """
        Initialize the agent with specified provider.

        Args:
            provider: "local", "groq", "google", "openai", or "auto"
        """
        self.provider = provider
        self.cv_summary = self._load_cv_summary()

        # Provider clients
        self._groq_client = None
        self._google_model = None
        self._openai_client = None

        # Check available providers
        self.available_providers = self._check_providers()

        # Set active provider
        if provider == "auto":
            self.active_provider = self._select_best_provider()
        else:
            self.active_provider = provider

    def _check_providers(self) -> dict:
        """Check which providers are available."""
        available = {"local": True}  # Local is always available

        # Check Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=groq_key)
                available["groq"] = True
            except Exception:
                available["groq"] = False
        else:
            available["groq"] = False

        # Check Google
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key and google_key != "your_google_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self._google_model = genai.GenerativeModel('gemini-1.5-flash')
                available["google"] = True
            except Exception:
                available["google"] = False
        else:
            available["google"] = False

        # Check OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=openai_key)
                available["openai"] = True
            except Exception:
                available["openai"] = False
        else:
            available["openai"] = False

        return available

    def _select_best_provider(self) -> str:
        """Select the best available provider."""
        # Priority: groq (free & fast) > google (free) > openai (paid) > local
        default = os.getenv("DEFAULT_LLM_PROVIDER", "groq")

        if self.available_providers.get(default):
            return default

        for provider in ["groq", "google", "openai", "local"]:
            if self.available_providers.get(provider):
                return provider
        return "local"

    def _load_cv_summary(self) -> str:
        """Load CV summary from file."""
        if CV_SUMMARY_FILE.exists():
            return CV_SUMMARY_FILE.read_text()
        return "No CV summary available. Please update data/cv_summary.txt"

    def _load_prompt_template(self, template_name: str) -> str:
        """Load a prompt template from the prompts directory."""
        template_path = PROMPTS_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        return template_path.read_text()

    def get_status(self) -> dict:
        """Get current agent status and available providers."""
        return {
            "active_provider": self.active_provider,
            "available_providers": self.available_providers,
            "cv_loaded": len(self.cv_summary) > 100
        }

    # =========================================================================
    # COVER LETTER GENERATION
    # =========================================================================

    def generate_cover_letter(
        self,
        company: str,
        role: str,
        job_description: str,
        provider: Optional[str] = None
    ) -> str:
        """
        Generate a tailored cover letter.

        Args:
            company: Company name
            role: Job title
            job_description: Full job description text
            provider: Override provider (optional)

        Returns:
            Generated cover letter text
        """
        use_provider = provider or self.active_provider

        if use_provider == "local":
            raise ValueError(
                "Local mode cannot generate cover letters. "
                "Please configure Groq or Google API key in .env file."
            )

        # Load prompt template
        prompt_template = self._load_prompt_template("cover_letter_prompt.txt")
        prompt = prompt_template.format(
            cv_summary=self.cv_summary,
            company=company,
            role=role,
            job_description=job_description
        )

        # Route to provider
        if use_provider == "groq":
            return self._generate_groq(prompt)
        elif use_provider == "google":
            return self._generate_google(prompt)
        elif use_provider == "openai":
            return self._generate_openai(prompt)
        else:
            raise ValueError(f"Unknown provider: {use_provider}")

    def _generate_groq(self, prompt: str) -> str:
        """Generate using Groq (Llama models)."""
        if not self._groq_client:
            raise ValueError("Groq client not initialized. Check GROQ_API_KEY.")

        response = self._groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Best free model
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional career advisor and cover letter writer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()

    def _generate_google(self, prompt: str) -> str:
        """Generate using Google Gemini."""
        if not self._google_model:
            raise ValueError("Google model not initialized. Check GOOGLE_API_KEY.")

        full_prompt = f"""You are a professional career advisor and cover letter writer.

{prompt}"""

        response = self._google_model.generate_content(full_prompt)
        return response.text.strip()

    def _generate_openai(self, prompt: str) -> str:
        """Generate using OpenAI."""
        if not self._openai_client:
            raise ValueError("OpenAI client not initialized. Check OPENAI_API_KEY.")

        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional career advisor and cover letter writer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()

    # =========================================================================
    # JOB FIT ANALYSIS
    # =========================================================================

    def analyze_job_fit(
        self,
        job_description: str,
        provider: Optional[str] = None,
        force_local: bool = False
    ) -> dict:
        """
        Analyze how well the candidate fits the job requirements.

        Args:
            job_description: Full job description text
            provider: Override provider (optional)
            force_local: Force local analysis (free, fast)

        Returns:
            Dict with fit analysis
        """
        # Use local if requested or if no cloud provider available
        if force_local:
            return self._analyze_local(job_description)

        use_provider = provider or self.active_provider

        if use_provider == "local":
            return self._analyze_local(job_description)

        # Try cloud analysis with fallback to local
        try:
            if use_provider == "groq":
                return self._analyze_groq(job_description)
            elif use_provider == "google":
                return self._analyze_google(job_description)
            elif use_provider == "openai":
                return self._analyze_openai(job_description)
        except Exception as e:
            # Fallback to local
            result = self._analyze_local(job_description)
            result["cloud_error"] = str(e)
            return result

        return self._analyze_local(job_description)

    def _analyze_local(self, job_description: str) -> dict:
        """Local keyword-based job fit analysis."""
        from tools.local_analyzer import analyze_job_fit_local
        result = analyze_job_fit_local(job_description)

        return {
            'fit_score': result.get('fit_score', 0),
            'strengths': result.get('technical_matches', []) + result.get('business_matches', []),
            'gaps': result.get('technical_gaps', []) + result.get('business_gaps', []),
            'recommendation': result.get('recommendation', 'Unknown'),
            'reasoning': f"Keyword matching: {len(result.get('technical_matches', []))} technical, {len(result.get('business_matches', []))} business matches",
            'analysis_type': 'local'
        }

    def _analyze_groq(self, job_description: str) -> dict:
        """Analyze using Groq."""
        prompt = self._build_analysis_prompt(job_description)

        response = self._groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brutally honest career advisor. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=500
        )

        result = self._parse_json_response(response.choices[0].message.content)
        result['analysis_type'] = 'groq'
        return result

    def _analyze_google(self, job_description: str) -> dict:
        """Analyze using Google Gemini."""
        prompt = f"""You are a brutally honest career advisor.

{self._build_analysis_prompt(job_description)}

Respond ONLY with valid JSON, no other text."""

        response = self._google_model.generate_content(prompt)
        result = self._parse_json_response(response.text)
        result['analysis_type'] = 'google'
        return result

    def _analyze_openai(self, job_description: str) -> dict:
        """Analyze using OpenAI."""
        prompt = self._build_analysis_prompt(job_description)

        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brutally honest career advisor. Analyze job fit objectively."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        result['analysis_type'] = 'openai'
        return result

    def _build_analysis_prompt(self, job_description: str) -> str:
        """Build the analysis prompt."""
        return f"""Analyze this job description against the candidate's background.

CANDIDATE BACKGROUND:
{self.cv_summary}

JOB DESCRIPTION:
{job_description}

Provide a JSON response with:
{{
    "fit_score": <1-10 score>,
    "strengths": [<list of 3-5 matching strengths>],
    "gaps": [<list of missing requirements>],
    "recommendation": "<Strong Apply|Apply|Consider|Skip>",
    "reasoning": "<brief explanation>"
}}"""

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            text = "\n".join(lines[1:-1])

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            # Return default if parsing fails
            return {
                "fit_score": 5,
                "strengths": [],
                "gaps": [],
                "recommendation": "Consider",
                "reasoning": "Could not parse AI response"
            }

    # =========================================================================
    # CV SUGGESTIONS
    # =========================================================================

    def generate_cv_suggestions(
        self,
        job_description: str,
        company: str,
        role: str,
        fit_analysis: Optional[dict] = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Generate specific suggestions for tailoring CV to this job.

        Args:
            job_description: Full job description
            company: Company name
            role: Job title
            fit_analysis: Previous fit analysis results (optional)
            provider: Override provider

        Returns:
            Text with CV customization suggestions
        """
        use_provider = provider or self.active_provider

        if use_provider == "local":
            return self._cv_suggestions_local(job_description, fit_analysis)

        prompt = self._build_cv_suggestions_prompt(job_description, company, role, fit_analysis)

        try:
            if use_provider == "groq":
                return self._cv_suggestions_groq(prompt)
            elif use_provider == "google":
                return self._cv_suggestions_google(prompt)
            elif use_provider == "openai":
                return self._cv_suggestions_openai(prompt)
        except Exception as e:
            # Fallback to local
            return self._cv_suggestions_local(job_description, fit_analysis) + f"\n\n(Cloud unavailable: {e})"

        return self._cv_suggestions_local(job_description, fit_analysis)

    def _build_cv_suggestions_prompt(
        self,
        job_description: str,
        company: str,
        role: str,
        fit_analysis: Optional[dict] = None
    ) -> str:
        """Build prompt for CV suggestions."""
        analysis_context = ""
        if fit_analysis:
            analysis_context = f"""
PREVIOUS FIT ANALYSIS:
- Score: {fit_analysis.get('fit_score', 'N/A')}/10
- Strengths: {', '.join(fit_analysis.get('strengths', [])[:5])}
- Gaps: {', '.join(fit_analysis.get('gaps', [])[:5])}
"""

        return f"""You are an expert CV/resume advisor. Based on the job description and candidate's current CV, provide specific, actionable suggestions for tailoring the CV to this role.

CURRENT CV SUMMARY:
{self.cv_summary}

TARGET ROLE: {role} at {company}

JOB DESCRIPTION:
{job_description}
{analysis_context}

Provide practical CV customization suggestions:

1. **KEY SKILLS TO HIGHLIGHT** - Which existing skills should be moved up/emphasized
2. **EXPERIENCE REFRAMING** - How to reword experience bullet points to match JD keywords
3. **KEYWORDS TO ADD** - Specific terms from the JD to incorporate
4. **SECTIONS TO ADJUST** - Any structural changes (order, emphasis)
5. **GAPS TO ADDRESS** - How to position around missing requirements

Be specific and reference actual content from the CV. Focus on what CAN be done, not what's missing."""

    def _cv_suggestions_groq(self, prompt: str) -> str:
        """Generate CV suggestions using Groq."""
        response = self._groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert CV/resume advisor. Provide actionable, specific suggestions."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()

    def _cv_suggestions_google(self, prompt: str) -> str:
        """Generate CV suggestions using Google."""
        full_prompt = f"You are an expert CV/resume advisor.\n\n{prompt}"
        response = self._google_model.generate_content(full_prompt)
        return response.text.strip()

    def _cv_suggestions_openai(self, prompt: str) -> str:
        """Generate CV suggestions using OpenAI."""
        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert CV/resume advisor."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()

    def _cv_suggestions_local(self, job_description: str, fit_analysis: Optional[dict] = None) -> str:
        """Generate basic CV suggestions using keyword matching."""
        from tools.local_analyzer import extract_keywords

        jd_keywords = extract_keywords(job_description)
        cv_keywords = extract_keywords(self.cv_summary)

        # Find overlapping and missing keywords
        jd_tech = set(jd_keywords.get('technical', []))
        jd_biz = set(jd_keywords.get('business', []))
        cv_tech = set(cv_keywords.get('technical', []))
        cv_biz = set(cv_keywords.get('business', []))

        matched_tech = jd_tech & cv_tech
        missing_tech = jd_tech - cv_tech
        matched_biz = jd_biz & cv_biz

        suggestions = []
        suggestions.append("## CV Customization Suggestions (Local Analysis)\n")

        if matched_tech:
            suggestions.append("### Skills to Highlight")
            suggestions.append("Move these to the top of your skills section:")
            for skill in list(matched_tech)[:8]:
                suggestions.append(f"- {skill}")

        if matched_biz:
            suggestions.append("\n### Business Keywords to Emphasize")
            suggestions.append("Include these terms in your experience descriptions:")
            for skill in list(matched_biz)[:5]:
                suggestions.append(f"- {skill}")

        if missing_tech:
            suggestions.append("\n### Keywords to Consider Adding")
            suggestions.append("If you have related experience, add these terms:")
            for skill in list(missing_tech)[:5]:
                suggestions.append(f"- {skill}")

        suggestions.append("\n### General Tips")
        suggestions.append("- Mirror the job description's language where truthful")
        suggestions.append("- Quantify achievements with numbers where possible")
        suggestions.append("- Lead with your most relevant experience for this role")

        return "\n".join(suggestions)

    # =========================================================================
    # HOLISTIC CV ANALYSIS
    # =========================================================================

    def analyze_cv_holistic(
        self,
        job_descriptions: list,
        job_metadata: list = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Analyse all collected job descriptions together and return holistic CV improvement advice.

        Args:
            job_descriptions: List of job description strings
            job_metadata: Optional list of dicts with company, role, score
            provider: AI provider to use
        """
        use_provider = provider or self.provider

        # Build a condensed summary of common requirements
        # Sample up to 20 JDs to avoid token overflow
        sample = job_descriptions[:20]
        combined = "\n\n---\n\n".join(
            f"[Job {i+1}{': ' + meta['role'] + ' @ ' + meta['company'] if meta else ''}]\n{jd[:800]}"
            for i, (jd, meta) in enumerate(zip(sample, (job_metadata or [{}]*len(sample))))
        )

        prompt = f"""You are an expert CV/resume strategist. Analyse the following {len(sample)} job descriptions (sampled from {len(job_descriptions)} total) that a candidate is targeting.

CANDIDATE'S CURRENT CV SUMMARY:
{self.cv_summary}

JOB DESCRIPTIONS (sample):
{combined}

Based on ALL these roles together, provide strategic CV improvement recommendations:

1. **RECURRING SKILLS TO ADD OR EMPHASISE** — Skills/keywords appearing across multiple JDs that should be more prominent
2. **EXPERIENCE TO REFRAME** — How to reword existing experience to match the language these employers use
3. **GAPS TO ADDRESS** — Common requirements the CV is missing and how to position around them
4. **CV STRUCTURE CHANGES** — Any sections to reorganise, add, or remove based on what these roles value
5. **SUMMARY/HEADLINE** — Suggested professional summary tailored to this target role profile

Focus on patterns across ALL roles, not just one. Be specific and actionable."""

        if use_provider == "auto":
            # Cascade through available providers
            if self.available_providers.get("groq"):
                return self._cv_suggestions_groq(prompt)
            elif self.available_providers.get("google"):
                return self._cv_suggestions_google(prompt)
            elif self.available_providers.get("openai"):
                return self._cv_suggestions_openai(prompt)
        elif use_provider == "groq":
            return self._cv_suggestions_groq(prompt)
        elif use_provider == "google":
            return self._cv_suggestions_google(prompt)
        elif use_provider == "openai":
            return self._cv_suggestions_openai(prompt)

        # Fallback: local keyword analysis across all JDs
        from tools.local_analyzer import extract_keywords
        all_keywords: dict = {}
        for jd in job_descriptions:
            for kw in extract_keywords(jd):
                all_keywords[kw] = all_keywords.get(kw, 0) + 1

        top_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:30]
        lines = ["**Top recurring keywords across all job descriptions:**\n"]
        lines += [f"- **{kw}** (appears in {count} jobs)" for kw, count in top_keywords]
        lines.append("\n_For detailed recommendations, configure a cloud AI provider (Groq or Google are free)._")
        return "\n".join(lines)

    # =========================================================================
    # FULL APPLICATION WORKFLOW
    # =========================================================================

    def process_full_application(
        self,
        company: str,
        role: str,
        job_description: str,
        job_url: Optional[str] = None,
        generate_cover_letter: bool = True,
        generate_cv_tips: bool = True,
        provider: Optional[str] = None
    ) -> dict:
        """
        Complete application workflow: analyze, generate cover letter, get CV tips.

        Returns dict with all generated content and analysis.
        """
        result = {
            "company": company,
            "role": role,
            "job_url": job_url,
            "job_description": job_description,
        }

        # Step 1: Analyze fit (always use local for speed, then optionally cloud)
        fit_analysis = self.analyze_job_fit(job_description, force_local=True)
        result["fit_analysis"] = fit_analysis
        result["fit_score"] = fit_analysis.get("fit_score", 0)

        # Get role categorization
        from tools.job_analyzer import categorize_role
        role_info = categorize_role(role, job_description)
        result["role_category"] = role_info.get("category", "other")
        result["seniority_level"] = role_info.get("seniority", "mid")

        # Step 2: Generate cover letter (if requested and cloud available)
        if generate_cover_letter:
            use_provider = provider or self.active_provider
            if use_provider != "local":
                try:
                    result["cover_letter"] = self.generate_cover_letter(
                        company, role, job_description, provider=use_provider
                    )
                except Exception as e:
                    result["cover_letter_error"] = str(e)
            else:
                result["cover_letter_error"] = "Cover letter requires cloud provider (Groq or Google)"

        # Step 3: Generate CV suggestions (if requested)
        if generate_cv_tips:
            use_provider = provider or self.active_provider
            try:
                result["cv_suggestions"] = self.generate_cv_suggestions(
                    job_description, company, role, fit_analysis, provider=use_provider
                )
            except Exception as e:
                result["cv_suggestions"] = self._cv_suggestions_local(job_description, fit_analysis)
                result["cv_suggestions_note"] = f"Using local analysis ({e})"

        return result


# CLI for testing
if __name__ == "__main__":
    print("🤖 Testing Multi-Provider Application Agent\n")

    agent = ApplicationAgent(provider="auto")
    status = agent.get_status()

    print(f"📊 Agent Status:")
    print(f"  Active Provider: {status['active_provider']}")
    print(f"  CV Loaded: {status['cv_loaded']}")
    print(f"\n  Available Providers:")
    for provider, available in status['available_providers'].items():
        icon = "✓" if available else "✗"
        print(f"    {icon} {provider}")

    # Test with sample JD
    test_jd = """
    We are looking for a Solutions Architect with experience in:
    - Python programming and data analysis
    - AWS cloud services
    - Data governance experience
    - Financial services preferred
    - Stakeholder management
    """

    print(f"\n🔍 Testing job fit analysis...")

    # Test local analysis
    print(f"\n  Local Analysis:")
    result = agent.analyze_job_fit(test_jd, force_local=True)
    print(f"    Score: {result['fit_score']}/10")
    print(f"    Recommendation: {result['recommendation']}")

    # Test cloud analysis if available
    if status['active_provider'] != 'local':
        print(f"\n  Cloud Analysis ({status['active_provider']}):")
        try:
            result = agent.analyze_job_fit(test_jd)
            print(f"    Score: {result['fit_score']}/10")
            print(f"    Recommendation: {result['recommendation']}")
            print(f"    Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
        except Exception as e:
            print(f"    Error: {e}")

    print("\n✅ Agent test complete!")
