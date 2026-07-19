import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base

# DB location is configurable via APP_DB_PATH so a demo/seed DB can be used
# without touching your real applications.db. Defaults to the original path.
DB_PATH = os.getenv("APP_DB_PATH", "applications.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database and run migrations."""
    Base.metadata.create_all(engine)
    run_migrations()


def run_migrations():
    """Add new columns to existing tables (safe for SQLite)."""
    migrations = [
        # Application table new columns
        ("applications", "fit_score", "REAL"),
        ("applications", "fit_analysis_json", "TEXT"),
        ("applications", "role_category", "VARCHAR"),
        ("applications", "seniority_level", "VARCHAR"),
        ("applications", "cover_letter_text", "TEXT"),
        ("applications", "cv_suggestions", "TEXT"),
        ("applications", "created_at", "DATETIME"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
                print(f"Added column: {table}.{column}")
            except Exception as e:
                # Column likely already exists
                if "duplicate column" not in str(e).lower():
                    pass  # Silently ignore if column exists
