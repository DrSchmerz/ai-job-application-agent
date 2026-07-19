#!/usr/bin/env python3
"""Seed a demo database with fake applications so the app runs for a showcase.

By default this writes to a dedicated `applications_demo.db` so your real
`applications.db` is never touched.

Usage:
    python scripts/seed_demo_data.py                 # -> applications_demo.db
    python scripts/seed_demo_data.py --force         # add rows even if DB not empty
    APP_DB_PATH=applications.db python scripts/seed_demo_data.py   # target a specific DB

Run the app against the demo DB:
    APP_DB_PATH=applications_demo.db streamlit run ui/app.py
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Default to a dedicated demo DB unless the caller specified one.
os.environ.setdefault("APP_DB_PATH", "applications_demo.db")

# Make project root importable regardless of where this is run from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.models import Application  # noqa: E402
from db.session import DB_PATH, SessionLocal, init_db  # noqa: E402

_NOW = datetime.utcnow()

SAMPLE_APPLICATIONS = [
    dict(
        company="Northwind Analytics",
        role="Data Scientist",
        job_url="https://example.com/jobs/data-scientist",
        status="Applied",
        application_date=_NOW - timedelta(days=12),
        fit_score=8.2,
        role_category="data_scientist",
        seniority_level="mid",
        notes="Referred by a former classmate.",
    ),
    dict(
        company="Helios Cloud",
        role="AI Solutions Engineer",
        job_url="https://example.com/jobs/ai-solutions-engineer",
        status="Interview",
        application_date=_NOW - timedelta(days=20),
        fit_score=9.1,
        role_category="solutions_engineer",
        seniority_level="mid",
        notes="First round scheduled. Prep system-design + product story.",
    ),
    dict(
        company="Cobalt Retail",
        role="Machine Learning Engineer",
        job_url="https://example.com/jobs/ml-engineer",
        status="Offer",
        application_date=_NOW - timedelta(days=34),
        fit_score=8.7,
        role_category="ml_engineer",
        seniority_level="mid",
        notes="Offer received — negotiating start date.",
    ),
    dict(
        company="Aurora Fintech",
        role="Data Engineer",
        job_url="https://example.com/jobs/data-engineer",
        status="Rejected",
        application_date=_NOW - timedelta(days=41),
        fit_score=6.4,
        role_category="data_engineer",
        seniority_level="junior",
        notes="Rejected after screening — wanted more Spark experience.",
    ),
    dict(
        company="Meridian Consulting",
        role="Analytics Consultant",
        job_url="https://example.com/jobs/analytics-consultant",
        status="Draft",
        fit_score=7.5,
        role_category="consultant",
        seniority_level="mid",
        notes="Draft — tailor cover letter before applying.",
    ),
    dict(
        company="Vertex Robotics",
        role="Applied Scientist",
        job_url="https://example.com/jobs/applied-scientist",
        status="Applied",
        application_date=_NOW - timedelta(days=5),
        fit_score=7.9,
        role_category="research",
        seniority_level="mid",
        notes="Waiting on response.",
    ),
]


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        existing = session.query(Application).count()
        if existing and "--force" not in sys.argv:
            print(
                f"DB '{DB_PATH}' already has {existing} application(s). "
                f"Use --force to add the sample rows anyway."
            )
            return

        for row in SAMPLE_APPLICATIONS:
            session.add(Application(created_at=_NOW, **row))
        session.commit()
        print(f"Seeded {len(SAMPLE_APPLICATIONS)} sample applications into '{DB_PATH}'.")
        print(f"Run:  APP_DB_PATH={DB_PATH} streamlit run ui/app.py")
    finally:
        session.close()


if __name__ == "__main__":
    main()
