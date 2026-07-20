"""Tests for email→application matching — the code that auto-updates statuses.

Guards against the substring bugs that made company "SAP" match sender
"asap-jobs@indeed.com" and auto-update the wrong application.
"""
from tools.email_automation import _company_matches, EmailAutomation, MatchedApp


class TestCompanyMatches:
    def test_exact_company_in_sender(self):
        assert _company_matches("Acme", "recruiting@acme.com your application")

    def test_company_in_subject(self):
        assert _company_matches("Datadog", "no-reply@greenhouse.io interview with datadog")

    def test_substring_false_positive_rejected(self):
        # 'sap' inside 'asap' must NOT match
        assert not _company_matches("SAP", "asap-jobs@indeed.com new jobs for you")

    def test_multiword_requires_all_significant_words(self):
        assert _company_matches("The Trade Desk", "careers@thetradedesk.com trade desk update")
        # 'the' + 'desk' alone (old >=2-any-words rule) must NOT match
        assert not _company_matches("The Trade Desk", "help@ikea.com your desk order and the delivery")

    def test_corporate_suffixes_ignored(self):
        assert _company_matches("Acme GmbH", "jobs@acme.com application update")

    def test_empty_company_never_matches(self):
        assert not _company_matches("", "anything@anywhere.com")


class TestShouldUpdateStatus:
    def _auto(self):
        # Build without __init__ (no Gmail/analyzer needed for this pure logic)
        return EmailAutomation.__new__(EmailAutomation)

    def _app(self, status="Applied"):
        return MatchedApp(id=1, company="Acme", role="DS", status=status)

    def test_low_confidence_blocked(self):
        auto = self._auto()
        email = {"suggested_status": "Interview", "confidence": 0.65}
        assert auto._should_update_status(self._app(), email) is False

    def test_high_confidence_forward_progression_allowed(self):
        auto = self._auto()
        email = {"suggested_status": "Interview", "confidence": 0.9}
        assert auto._should_update_status(self._app("Applied"), email) is True

    def test_no_backwards_progression(self):
        auto = self._auto()
        email = {"suggested_status": "Applied", "confidence": 0.9}
        assert auto._should_update_status(self._app("Interview"), email) is False

    def test_rejection_always_allowed(self):
        auto = self._auto()
        email = {"suggested_status": "Rejected", "confidence": 0.9}
        assert auto._should_update_status(self._app("Interview"), email) is True
