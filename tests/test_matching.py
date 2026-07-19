"""Tests for core.matching — especially the substring-matching bug fix."""
from core import matching


class TestBoundaryMatching:
    """The old code used ``skill in text`` which matched inside words. These guard against that."""

    def test_short_token_not_matched_inside_word(self):
        assert matching.skill_in_text("ai", "email") is False
        assert matching.skill_in_text("ai", "available") is False
        assert matching.skill_in_text("r", "requirements") is False
        assert matching.skill_in_text("go", "good communication") is False
        assert matching.skill_in_text("ml", "html") is False

    def test_token_matched_as_whole_word(self):
        assert matching.skill_in_text("ai", "experience with AI and ML") is True
        assert matching.skill_in_text("r", "fluent in R and Python") is True
        assert matching.skill_in_text("go", "we use Go for backend") is True

    def test_symbol_bearing_skills(self):
        assert matching.skill_in_text("c++", "strong C++ background") is True
        assert matching.skill_in_text("ci/cd", "owns the CI/CD pipeline") is True
        assert matching.skill_in_text("c++", "abc++def") is False

    def test_multiword_phrases(self):
        assert matching.skill_in_text("machine learning", "applied Machine Learning daily") is True
        assert matching.skill_in_text("data governance", "led data governance initiatives") is True


class TestExtractSkills:
    def test_extracts_known_skills(self):
        jd = "We need Python, SQL, AWS and stakeholder management. Docker is a plus."
        skills = matching.extract_skills(jd)
        assert "python" in skills["technical"]
        assert "sql" in skills["technical"]
        assert "aws" in skills["technical"]
        assert "docker" in skills["technical"]
        assert "stakeholder" in skills["business"]

    def test_no_false_positive_from_substrings(self):
        # "email" must not surface "ai"; "algorithms" must not surface "r"/"go"
        skills = matching.extract_skills("Send an email about our algorithms.")
        assert "ai" not in skills["technical"]
        assert "r" not in skills["technical"]
        assert "go" not in skills["technical"]


class TestFitScore:
    def test_score_is_bounded(self):
        empty = {"technical": {"matched": [], "missing": []},
                 "business": {"matched": [], "missing": []}}
        score, rec = matching.compute_fit_score(empty)
        assert 1 <= score <= 10
        assert rec in {"Strong Apply", "Apply", "Consider", "Weak Fit"}

    def test_full_match_scores_high(self):
        full = {"technical": {"matched": ["python", "sql", "aws"], "missing": []},
                "business": {"matched": ["stakeholder"], "missing": []}}
        score, rec = matching.compute_fit_score(full)
        assert score == 10
        assert rec == "Strong Apply"

    def test_poor_match_scores_low(self):
        poor = {"technical": {"matched": [], "missing": ["python", "sql", "aws", "docker"]},
                "business": {"matched": [], "missing": ["stakeholder", "leadership"]}}
        score, _ = matching.compute_fit_score(poor)
        assert score <= 3

    def test_analyze_fit_end_to_end(self):
        cv = "Data scientist skilled in Python, SQL, pandas and stakeholder communication."
        jd = "Looking for Python, SQL, Spark and stakeholder management."
        result = matching.analyze_fit(jd, cv)
        assert result["fit_score"] >= 1
        assert "python" in result["technical_matches"]
        assert "spark" in result["technical_gaps"]

    def test_analyze_fit_no_cv(self):
        assert matching.analyze_fit("anything", "")["fit_score"] == 0
