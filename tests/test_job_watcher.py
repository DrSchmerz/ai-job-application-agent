"""Tests for the target-company job watcher (board detection + persistence)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, JobPosting
from tools.job_watcher import parse_board_from_url, slug_candidates, upsert_postings


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


class TestBoardDetection:
    def test_greenhouse_urls(self):
        assert parse_board_from_url("https://boards.greenhouse.io/anthropic") == ("greenhouse", "anthropic")
        assert parse_board_from_url("https://job-boards.greenhouse.io/datadog/jobs/123") == ("greenhouse", "datadog")

    def test_lever_urls(self):
        assert parse_board_from_url("https://jobs.lever.co/spotify") == ("lever", "spotify")
        assert parse_board_from_url("https://jobs.lever.co/company-x/uuid-here") == ("lever", "company-x")

    def test_non_board_urls(self):
        assert parse_board_from_url("https://careers.example.com/jobs") is None
        assert parse_board_from_url("") is None

    def test_slug_candidates(self):
        assert slug_candidates("The Trade Desk") == ["thetradedesk", "the-trade-desk"]
        assert slug_candidates("Anthropic") == ["anthropic"]
        assert slug_candidates("") == []


def _posting(ext_id="j1", title="Data Scientist", desc="Python SQL machine learning"):
    return {"source": "greenhouse", "external_id": ext_id, "title": title,
            "location": "Berlin", "url": f"https://x/{ext_id}", "description": desc}


CV = "Data scientist with Python, SQL, pandas and machine learning experience."


class TestUpsert:
    def test_new_postings_are_inserted_and_scored(self, db):
        counts = upsert_postings(db, "Acme", [_posting()], CV)
        assert counts == {"new": 1, "seen": 0}
        row = db.query(JobPosting).one()
        assert row.company == "Acme"
        assert row.fit_score and row.fit_score >= 5  # strong overlap with CV

    def test_rescan_marks_seen_not_duplicate(self, db):
        upsert_postings(db, "Acme", [_posting()], CV)
        counts = upsert_postings(db, "Acme", [_posting()], CV)
        assert counts == {"new": 0, "seen": 1}
        assert db.query(JobPosting).count() == 1  # no duplicate rows

    def test_vanished_posting_marked_inactive(self, db):
        upsert_postings(db, "Acme", [_posting("j1"), _posting("j2", title="ML Engineer")], CV)
        upsert_postings(db, "Acme", [_posting("j1")], CV)  # j2 gone from the board
        j2 = db.query(JobPosting).filter(JobPosting.external_id == "j2").one()
        assert j2.is_active == 0
        j1 = db.query(JobPosting).filter(JobPosting.external_id == "j1").one()
        assert j1.is_active == 1

    def test_other_companies_untouched_by_inactive_sweep(self, db):
        upsert_postings(db, "Acme", [_posting("a1")], CV)
        upsert_postings(db, "Globex", [_posting("g1")], CV)
        # Rescan Acme only — Globex's posting must stay active
        upsert_postings(db, "Acme", [_posting("a1")], CV)
        g1 = db.query(JobPosting).filter(JobPosting.external_id == "g1").one()
        assert g1.is_active == 1

    def test_posting_without_id_skipped(self, db):
        counts = upsert_postings(db, "Acme", [_posting(ext_id="")], CV)
        assert counts == {"new": 0, "seen": 0}
        assert db.query(JobPosting).count() == 0
