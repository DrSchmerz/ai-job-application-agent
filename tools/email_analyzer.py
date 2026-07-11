"""
LLM-powered Email Analyzer for job application tracking.
Classifies emails and extracts relevant information for application status updates.
"""
import os
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
sys.path.insert(0, str(PROJECT_ROOT))


class EmailAnalyzer:
    """
    Analyze application-related emails using LLM or local keyword matching.

    Supports multiple providers:
    - groq: Fast, free tier available
    - google: Gemini, free tier available
    - openai: GPT models, paid
    - local: Keyword-based fallback (no API needed)
    """

    # Keywords for local analysis
    REJECTION_KEYWORDS = [
        "unfortunately", "regret to inform", "not moving forward",
        "decided not to proceed", "other candidates", "not selected",
        "after careful consideration", "will not be advancing",
        "position has been filled", "gone with another candidate"
    ]

    INTERVIEW_KEYWORDS = [
        "interview", "schedule", "meet with", "speak with",
        "availability", "call with", "discuss your application",
        "next steps", "would like to invite", "phone screen",
        "technical interview", "video call", "zoom", "teams call"
    ]

    OFFER_KEYWORDS = [
        "pleased to offer", "job offer", "offer letter",
        "excited to extend", "formal offer", "compensation",
        "start date", "accept the position", "welcome to the team"
    ]

    SCHEDULING_KEYWORDS = [
        "reschedule", "confirm the time", "calendar invite",
        "available on", "book a time", "let me know when",
        "schedule a call", "set up a meeting"
    ]

    INFO_REQUEST_KEYWORDS = [
        "additional information", "references", "portfolio",
        "work samples", "provide", "send us", "need from you",
        "required documents", "background check"
    ]

    def __init__(self, provider: str = "auto"):
        """
        Initialize the email analyzer.

        Args:
            provider: LLM provider to use (groq, google, openai, local, auto)
        """
        self.provider = provider
        self._groq_client = None
        self._google_model = None
        self._openai_client = None

        # Initialize providers
        self.available_providers = self._check_providers()

        # Select active provider
        if provider == "auto":
            self.active_provider = self._select_best_provider()
        else:
            self.active_provider = provider if self.available_providers.get(provider) else "local"

    def _check_providers(self) -> Dict[str, bool]:
        """Check which LLM providers are available."""
        available = {"local": True}

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
        for provider in ["groq", "google", "openai", "local"]:
            if self.available_providers.get(provider):
                return provider
        return "local"

    def _load_prompt_template(self) -> str:
        """Load the email analysis prompt template."""
        template_path = PROMPTS_DIR / "email_analysis_prompt.txt"
        if template_path.exists():
            return template_path.read_text()

        # Fallback prompt if file not found
        return """Analyze this email and respond with JSON:
Subject: {subject}
From: {sender}
Body: {body}

Return JSON with: email_type, confidence, summary, extracted_date, extracted_time, next_steps, suggested_status, key_details"""

    def analyze_email(
        self,
        subject: str,
        sender: str,
        body: str,
        date: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an email to classify it and extract relevant information.

        Args:
            subject: Email subject line
            sender: Sender email/name
            body: Email body text
            date: Email date (optional)
            provider: Override provider for this analysis

        Returns:
            Dictionary with analysis results:
            - email_type: Classification (rejection, interview_invite, etc.)
            - confidence: 0-1 confidence score
            - summary: One sentence summary
            - extracted_date: Any date mentioned (YYYY-MM-DD)
            - extracted_time: Any time mentioned (HH:MM)
            - next_steps: List of action items
            - suggested_status: Suggested application status update
            - key_details: Additional extracted information
        """
        use_provider = provider or self.active_provider

        # Use LLM if available, otherwise fall back to local
        if use_provider == "local" or not self.available_providers.get(use_provider, False):
            return self._analyze_local(subject, sender, body)

        try:
            return self._analyze_with_llm(subject, sender, body, date, use_provider)
        except Exception as e:
            print(f"LLM analysis failed ({use_provider}): {e}")
            return self._analyze_local(subject, sender, body)

    def _analyze_with_llm(
        self,
        subject: str,
        sender: str,
        body: str,
        date: Optional[str],
        provider: str
    ) -> Dict[str, Any]:
        """Analyze email using LLM provider."""
        # Build prompt
        template = self._load_prompt_template()
        prompt = template.format(
            subject=subject,
            sender=sender,
            date=date or "Unknown",
            body=body[:3000]  # Limit body length
        )

        # Call appropriate provider
        if provider == "groq":
            response = self._call_groq(prompt)
        elif provider == "google":
            response = self._call_google(prompt)
        elif provider == "openai":
            response = self._call_openai(prompt)
        else:
            return self._analyze_local(subject, sender, body)

        # Parse JSON response
        result = self._parse_llm_response(response)
        result["analysis_provider"] = provider
        return result

    def _call_groq(self, prompt: str) -> str:
        """Call Groq API."""
        response = self._groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an email analyzer. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API."""
        response = self._google_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 1000
            }
        )
        return response.text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an email analyzer. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if match:
                    response = match.group(1)
            elif "```" in response:
                match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if match:
                    response = match.group(1)

            result = json.loads(response.strip())

            # Ensure required fields
            return {
                "email_type": result.get("email_type", "other"),
                "confidence": float(result.get("confidence", 0.5)),
                "summary": result.get("summary", ""),
                "extracted_date": result.get("extracted_date"),
                "extracted_time": result.get("extracted_time"),
                "next_steps": result.get("next_steps", []),
                "suggested_status": result.get("suggested_status"),
                "key_details": result.get("key_details", {})
            }
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse LLM response: {e}")
            return self._get_default_response()

    def _analyze_local(self, subject: str, sender: str, body: str) -> Dict[str, Any]:
        """
        Analyze email using local keyword matching.
        Fallback when LLM is not available.
        """
        combined_text = f"{subject} {body}".lower()

        # Count keyword matches for each category
        scores = {
            "rejection": self._count_matches(combined_text, self.REJECTION_KEYWORDS),
            "interview_invite": self._count_matches(combined_text, self.INTERVIEW_KEYWORDS),
            "offer": self._count_matches(combined_text, self.OFFER_KEYWORDS),
            "scheduling": self._count_matches(combined_text, self.SCHEDULING_KEYWORDS),
            "info_request": self._count_matches(combined_text, self.INFO_REQUEST_KEYWORDS)
        }

        # Determine type based on highest score
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]

        if max_score == 0:
            email_type = "other"
            confidence = 0.3
        else:
            email_type = max_type
            # Calculate confidence based on number of matches
            confidence = min(0.5 + (max_score * 0.15), 0.9)

        # Extract dates using regex
        extracted_date = self._extract_date(combined_text)
        extracted_time = self._extract_time(combined_text)

        # Generate next steps based on type
        next_steps = self._generate_next_steps(email_type)

        # Suggest status
        suggested_status = self._suggest_status(email_type)

        return {
            "email_type": email_type,
            "confidence": confidence,
            "summary": self._generate_summary(email_type, subject),
            "extracted_date": extracted_date,
            "extracted_time": extracted_time,
            "next_steps": next_steps,
            "suggested_status": suggested_status,
            "key_details": {},
            "analysis_provider": "local"
        }

    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords match in the text."""
        return sum(1 for kw in keywords if kw.lower() in text)

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text."""
        # Various date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}',
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(0)
                    # Try to parse and standardize
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y', '%B %d %Y', '%d %B %Y']:
                        try:
                            dt = datetime.strptime(date_str.replace(',', ''), fmt)
                            return dt.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                    return date_str
                except Exception:
                    continue
        return None

    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text."""
        # Time patterns
        patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}:\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                time_str = match.group(1)
                try:
                    # Try to parse and standardize to HH:MM
                    for fmt in ['%I:%M %p', '%I %p', '%H:%M']:
                        try:
                            dt = datetime.strptime(time_str.upper(), fmt)
                            return dt.strftime('%H:%M')
                        except ValueError:
                            continue
                    return time_str
                except Exception:
                    continue
        return None

    def _generate_next_steps(self, email_type: str) -> List[str]:
        """Generate suggested next steps based on email type."""
        steps = {
            "rejection": ["Update application status to Rejected", "Review feedback if provided"],
            "interview_invite": ["Respond to confirm availability", "Prepare for interview", "Research the company"],
            "offer": ["Review offer details carefully", "Respond within deadline", "Negotiate if needed"],
            "scheduling": ["Confirm the proposed time", "Add to calendar", "Prepare for the meeting"],
            "info_request": ["Gather requested information", "Respond promptly"],
            "confirmation": ["No action needed", "Keep tracking"],
            "other": []
        }
        return steps.get(email_type, [])

    def _suggest_status(self, email_type: str) -> Optional[str]:
        """Suggest application status based on email type."""
        status_map = {
            "rejection": "Rejected",
            "interview_invite": "Interview",
            "offer": "Offer",
            "scheduling": None,  # Keep current status
            "info_request": None,
            "confirmation": None,
            "other": None
        }
        return status_map.get(email_type)

    def _generate_summary(self, email_type: str, subject: str) -> str:
        """Generate a summary based on type and subject."""
        summaries = {
            "rejection": "Application was not successful",
            "interview_invite": "Interview invitation received",
            "offer": "Job offer received",
            "scheduling": "Interview scheduling communication",
            "info_request": "Request for additional information",
            "confirmation": "Application/interview confirmed",
            "other": f"Email regarding: {subject[:50]}"
        }
        return summaries.get(email_type, subject[:100])

    def _get_default_response(self) -> Dict[str, Any]:
        """Return default response structure."""
        return {
            "email_type": "other",
            "confidence": 0.0,
            "summary": "Could not analyze email",
            "extracted_date": None,
            "extracted_time": None,
            "next_steps": [],
            "suggested_status": None,
            "key_details": {},
            "analysis_provider": "error"
        }

    def batch_analyze(
        self,
        emails: List[Dict[str, str]],
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple emails.

        Args:
            emails: List of email dicts with subject, sender, body, date keys
            provider: Override provider

        Returns:
            List of analysis results
        """
        results = []
        for email_data in emails:
            result = self.analyze_email(
                subject=email_data.get("subject", ""),
                sender=email_data.get("from", email_data.get("sender", "")),
                body=email_data.get("body", email_data.get("snippet", "")),
                date=email_data.get("date"),
                provider=provider
            )
            result["email_id"] = email_data.get("id")
            result["original_subject"] = email_data.get("subject", "")
            result["original_sender"] = email_data.get("from", email_data.get("sender", ""))
            result["original_date"] = email_data.get("date")
            results.append(result)
        return results


# CLI for testing
if __name__ == "__main__":
    print("📧 Email Analyzer\n")

    analyzer = EmailAnalyzer()
    print(f"Active provider: {analyzer.active_provider}")
    print(f"Available providers: {analyzer.available_providers}")

    # Test email
    test_email = {
        "subject": "Interview Invitation - Software Engineer Position",
        "sender": "recruiter@company.com",
        "body": """
        Hi,

        Thank you for your application to the Software Engineer position at our company.

        We were impressed with your background and would like to invite you for a video interview.

        Are you available on January 15th, 2025 at 2:00 PM PST for a 45-minute call with our engineering team?

        Please confirm your availability.

        Best regards,
        HR Team
        """
    }

    print("\n--- Analyzing test email ---")
    result = analyzer.analyze_email(
        subject=test_email["subject"],
        sender=test_email["sender"],
        body=test_email["body"]
    )

    print(f"\nType: {result['email_type']}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Summary: {result['summary']}")
    print(f"Extracted date: {result['extracted_date']}")
    print(f"Extracted time: {result['extracted_time']}")
    print(f"Next steps: {result['next_steps']}")
    print(f"Suggested status: {result['suggested_status']}")
    print(f"Provider used: {result['analysis_provider']}")
