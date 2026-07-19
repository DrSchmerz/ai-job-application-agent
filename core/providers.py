"""
Unified LLM provider abstraction.

Previously the provider ladder (``if provider == "groq" ... elif "google" ...``) was
duplicated across ``agent/agent.py``, ``tools/email_analyzer.py`` and ``ui/app.py``.
This module is the single place that knows how to detect, select, and call a provider.

Supports Groq, Google Gemini, OpenAI, and a "local" no-LLM mode. Keys come from the
environment by default, but can be passed in — which makes a future "bring your own key"
multi-user mode straightforward.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional

# Priority order when provider == "auto" (free/fast first).
PRIORITY = ["groq", "google", "openai", "local"]

MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "google": "gemini-1.5-flash",  # TODO: migrate to the `google-genai` SDK + newer model
}

_PLACEHOLDERS = {"", "your_groq_api_key_here", "your_google_api_key_here",
                 "your_openai_api_key_here", "changeme"}


def _valid(key: Optional[str]) -> bool:
    return bool(key) and key.strip() not in _PLACEHOLDERS


def available_providers(keys: Dict[str, str]) -> Dict[str, bool]:
    """Which providers are usable given a dict of api keys. ``local`` is always True."""
    return {
        "local": True,
        "groq": _valid(keys.get("groq")),
        "google": _valid(keys.get("google")),
        "openai": _valid(keys.get("openai")),
    }


def select_provider(available: Dict[str, bool], preferred: str = "auto") -> str:
    """Pick a provider. Pure function so it is easy to test.

    If *preferred* is a concrete, available provider, use it; otherwise fall back through
    PRIORITY to the first available one (``local`` always works).
    """
    if preferred and preferred != "auto" and available.get(preferred):
        return preferred
    for p in PRIORITY:
        if available.get(p):
            return p
    return "local"


def parse_json(text: str) -> dict:
    """Best-effort JSON extraction from an LLM response (handles ``` fences / stray prose)."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    raise ValueError("Could not parse JSON from LLM response")


class LLMProvider:
    """Detects available providers and runs completions through a single interface."""

    def __init__(self, keys: Optional[Dict[str, str]] = None):
        if keys is None:
            keys = {
                "groq": os.getenv("GROQ_API_KEY", ""),
                "google": os.getenv("GOOGLE_API_KEY", ""),
                "openai": os.getenv("OPENAI_API_KEY", ""),
            }
        self.keys = keys
        self.available = available_providers(keys)
        self._clients: Dict[str, object] = {}

    def is_available(self, provider: str) -> bool:
        return bool(self.available.get(provider))

    def select(self, preferred: str = "auto") -> str:
        return select_provider(self.available, preferred)

    def complete(self, prompt: str, *, system: Optional[str] = None,
                 provider: str = "auto", json_mode: bool = False,
                 temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Run a completion. Raises if the resolved provider is ``local`` (no LLM)."""
        chosen = self.select(provider)
        if chosen == "local":
            raise RuntimeError("No LLM provider configured — set an API key in .env")
        return getattr(self, f"_complete_{chosen}")(
            prompt, system, json_mode, temperature, max_tokens
        )

    # --- provider backends --------------------------------------------------------

    def _complete_groq(self, prompt, system, json_mode, temperature, max_tokens):
        if "groq" not in self._clients:
            from groq import Groq
            self._clients["groq"] = Groq(api_key=self.keys["groq"])
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        resp = self._clients["groq"].chat.completions.create(
            model=MODELS["groq"], messages=messages,
            temperature=temperature, max_tokens=max_tokens)
        return resp.choices[0].message.content.strip()

    def _complete_openai(self, prompt, system, json_mode, temperature, max_tokens):
        if "openai" not in self._clients:
            from openai import OpenAI
            self._clients["openai"] = OpenAI(api_key=self.keys["openai"])
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        kwargs = {"model": MODELS["openai"], "messages": messages, "temperature": temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        else:
            kwargs["max_tokens"] = max_tokens
        resp = self._clients["openai"].chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()

    def _complete_google(self, prompt, system, json_mode, temperature, max_tokens):
        if "google" not in self._clients:
            import google.generativeai as genai
            genai.configure(api_key=self.keys["google"])
            self._clients["google"] = genai.GenerativeModel(MODELS["google"])
        parts = [p for p in (system, prompt) if p]
        if json_mode:
            parts.append("Respond ONLY with valid JSON, no other text.")
        resp = self._clients["google"].generate_content("\n\n".join(parts))
        return resp.text.strip()
