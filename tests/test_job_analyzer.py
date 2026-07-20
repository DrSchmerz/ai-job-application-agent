"""Regression tests for tools.job_analyzer — the substring-matching bugs.

Before the fix, seniority used `"i" in title` (substring) so any title containing
the letter "i" (e.g. "Sen-i-or Engineer") was classified as junior, and the "se"
title pattern gave +3 sales-engineer points to titles like "Senior Data Analyst".
"""
from tools.job_analyzer import categorize_role


class TestSeniority:
    def test_senior_titles_are_senior(self):
        assert categorize_role("Senior Data Engineer", "")["seniority"] == "senior"
        assert categorize_role("Principal Architect", "")["seniority"] == "senior"
        assert categorize_role("Lead Machine Learning Engineer", "")["seniority"] == "senior"

    def test_junior_titles_are_junior(self):
        assert categorize_role("Junior Data Analyst", "")["seniority"] == "junior"
        assert categorize_role("Graduate Consultant", "")["seniority"] == "junior"

    def test_plain_titles_default_to_mid(self):
        # These contain the letter "i" — the old substring match made them junior.
        assert categorize_role("Data Scientist", "")["seniority"] == "mid"
        assert categorize_role("Solutions Architect", "")["seniority"] == "mid"


class TestCategory:
    def test_sales_engineer_detected(self):
        result = categorize_role(
            "Sales Engineer",
            "You will run demos and POCs, own RFPs and work with the presales team.",
        )
        assert result["category"] == "sales_engineer"

    def test_senior_data_analyst_not_sales_engineer(self):
        # The old `"se" in title` substring gave this +3 sales-engineer points.
        result = categorize_role(
            "Senior Data Analyst",
            "SQL, dashboards, data pipeline work, analytics and BI reporting.",
        )
        assert result["category"] != "sales_engineer"

    def test_data_role_detected(self):
        result = categorize_role(
            "Data Engineer",
            "Build ETL data pipelines with Spark and Airflow. Data engineer role.",
        )
        assert result["category"] == "data_role"
