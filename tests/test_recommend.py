"""Tests for core.recommend — local (no-API) fallback."""
from core import recommend


def test_recommends_relevant_roles_for_ds_cv():
    cv = ("Data scientist with Python, pandas, scikit-learn, machine learning and SQL. "
          "Built analytics dashboards and worked with stakeholders.")
    result = recommend.recommend_roles(cv)  # no llm -> local fallback
    assert result["source"] == "local"
    titles = [r["title"] for r in result["recommendations"]]
    assert "Data Scientist" in titles
    assert result["recommendations"]  # non-empty


def test_top_n_is_respected():
    cv = "Python SQL machine learning analytics finance risk consulting stakeholder docker aws spark etl"
    result = recommend.recommend_roles(cv, top_n=3)
    assert len(result["recommendations"]) <= 3


def test_each_recommendation_has_search_terms():
    cv = "SQL, Tableau, Power BI, analytics, business intelligence."
    for rec in recommend.recommend_roles(cv)["recommendations"]:
        assert rec["title"]
        assert rec["search_terms"]
        assert rec["why"]


def test_empty_cv_returns_nothing():
    assert recommend.recommend_roles("")["recommendations"] == []
