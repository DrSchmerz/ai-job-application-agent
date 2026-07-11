"""
Migration: Add interview prep tables to database.
Run this once to create the new tables.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import engine
from db.models import Base
from db.interview_prep import InterviewPrep, PracticeQuestion, InterviewFeedback


def create_interview_prep_tables():
    """Create interview prep tables."""
    print("📚 Creating interview prep tables...\n")

    # Create all tables (will only create missing ones)
    Base.metadata.create_all(bind=engine)

    print("✅ Interview prep tables created successfully!")
    print("\nNew tables:")
    print("  - interview_prep (company research, prep notes)")
    print("  - practice_questions (questions and prepared answers)")
    print("  - interview_feedback (post-interview reflections)")
    print("\n🎯 Interview prep module is ready to use!")


if __name__ == "__main__":
    create_interview_prep_tables()
