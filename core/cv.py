"""
CV ingestion: extract text from an uploaded file and turn it into a structured profile.

This is the entry point for the multi-user direction — a user uploads a CV (PDF / DOCX /
TXT), we extract the text, and (optionally with an LLM) parse it into a structured profile
used for fit scoring, role recommendations, and cover letters.

Parsing has a **local fallback** (skill extraction via ``core.matching``) so it works
without any API key.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core import matching
from core.logging_config import get_logger
from core.providers import LLMProvider, parse_json

log = get_logger(__name__)

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


def extract_text(path: str | Path) -> str:
    """Extract raw text from a CV file (PDF, DOCX, TXT/MD)."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported CV format '{ext}'. Supported: {sorted(SUPPORTED)}")

    if ext in {".txt", ".md"}:
        return path.read_text(errors="ignore")

    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if ext == ".docx":
        import docx  # python-docx
        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs)

    return ""  # unreachable


_PARSE_PROMPT = """Extract a structured profile from this CV. Respond ONLY with JSON:
{{
  "name": "<full name or empty>",
  "headline": "<one-line professional summary>",
  "years_experience": <integer or null>,
  "skills": [<key technical and business skills>],
  "domains": [<industries / domains, e.g. finance, healthcare>]
}}

CV:
{cv_text}"""


def parse_cv(cv_text: str, llm: Optional[LLMProvider] = None, provider: str = "auto") -> Dict:
    """Parse CV text into a structured profile. Uses an LLM when available, else a
    deterministic local fallback (skill extraction)."""
    cv_text = (cv_text or "").strip()
    if not cv_text:
        return {"error": "empty CV", "skills": [], "source": "none"}

    if llm is not None and llm.select(provider) != "local":
        try:
            raw = llm.complete(
                _PARSE_PROMPT.format(cv_text=cv_text[:8000]),
                system="You are an expert technical recruiter.",
                provider=provider,
                json_mode=True,
                temperature=0.2,
            )
            data = parse_json(raw)
            data["source"] = "llm"
            return data
        except Exception as exc:  # fall back gracefully
            log.warning("LLM CV parse failed (%s); using local fallback", exc)

    skills = matching.extract_skills(cv_text)
    return {
        "name": "",
        "headline": cv_text.split("\n", 1)[0][:120],
        "years_experience": None,
        "skills": skills["technical"] + skills["business"],
        "domains": [],
        "source": "local",
    }
