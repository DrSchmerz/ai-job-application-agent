"""Tests for core.providers selection + JSON parsing (no network calls)."""
import pytest
from core import providers


class TestAvailability:
    def test_local_always_available(self):
        assert providers.available_providers({})["local"] is True

    def test_placeholder_keys_are_invalid(self):
        av = providers.available_providers({"groq": "your_groq_api_key_here", "openai": ""})
        assert av["groq"] is False
        assert av["openai"] is False

    def test_real_key_is_valid(self):
        assert providers.available_providers({"openai": "sk-realkey123"})["openai"] is True


class TestSelect:
    def test_prefers_explicit_available_provider(self):
        av = {"local": True, "groq": True, "openai": True, "google": False}
        assert providers.select_provider(av, "openai") == "openai"

    def test_falls_back_by_priority(self):
        av = {"local": True, "groq": False, "google": True, "openai": True}
        assert providers.select_provider(av, "auto") == "google"  # google before openai

    def test_unavailable_preferred_falls_back(self):
        av = {"local": True, "groq": True, "google": False, "openai": False}
        assert providers.select_provider(av, "google") == "groq"

    def test_no_keys_returns_local(self):
        assert providers.select_provider({"local": True}, "auto") == "local"


class TestParseJson:
    def test_plain_json(self):
        assert providers.parse_json('{"a": 1}') == {"a": 1}

    def test_fenced_json(self):
        assert providers.parse_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_json_with_surrounding_prose(self):
        assert providers.parse_json('Here you go:\n{"a": 1}\nHope that helps') == {"a": 1}

    def test_unparseable_raises(self):
        with pytest.raises(ValueError):
            providers.parse_json("not json at all")
