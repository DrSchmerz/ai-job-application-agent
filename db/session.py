import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.logging_config import get_logger
from db.models import Base

log = get_logger(__name__)


def _database_url() -> str:
    """Resolve the DB URL.

    - ``DATABASE_URL`` (e.g. Postgres for a deployed friends-beta) takes priority.
    - Otherwise fall back to a local SQLite file at ``APP_DB_PATH`` (default
      ``applications.db``) for single-user / local development.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        # Heroku/Render-style "postgres://" -> SQLAlchemy's "postgresql://"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return f"sqlite:///{os.getenv('APP_DB_PATH', 'applications.db')}"


DB_URL = _database_url()
_is_sqlite = DB_URL.startswith("sqlite")
# SQLite + Streamlit/background threads need check_same_thread disabled.
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(DB_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create tables and run lightweight column migrations."""
    Base.metadata.create_all(engine)
    _run_sqlite_migrations()


def _run_sqlite_migrations():
    """Add columns to pre-existing SQLite DBs. (No-op on Postgres, where
    ``create_all`` already builds new tables/columns.)"""
    if not _is_sqlite:
        return
    migrations = [
        ("applications", "fit_score", "REAL"),
        ("applications", "fit_analysis_json", "TEXT"),
        ("applications", "role_category", "VARCHAR"),
        ("applications", "seniority_level", "VARCHAR"),
        ("applications", "cover_letter_text", "TEXT"),
        ("applications", "cv_suggestions", "TEXT"),
        ("applications", "created_at", "DATETIME"),
        ("applications", "user_id", "INTEGER"),  # multi-user ownership
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
                log.debug("migration: added %s.%s", table, column)
            except Exception as exc:
                if "duplicate column" not in str(exc).lower():
                    pass  # column already exists — fine
