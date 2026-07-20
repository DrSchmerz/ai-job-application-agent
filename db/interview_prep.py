"""
Database models and functions for interview preparation.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from db.models import Base
from db.session import SessionLocal


class InterviewPrep(Base):
    """Store interview preparation materials for each application."""
    __tablename__ = "interview_prep"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    # Company Research
    company_research = Column(Text)  # Notes about the company
    company_culture = Column(Text)  # Culture notes
    recent_news = Column(Text)  # Recent news/developments

    # Role-Specific Prep
    key_skills = Column(Text)  # JSON array of key skills to highlight
    relevant_experience = Column(Text)  # Which experiences to emphasize

    # Practice Questions & Answers
    questions_practiced = Column(Integer, default=0)  # Count of practiced questions
    practice_time_minutes = Column(Integer, default=0)  # Total practice time

    # Interview Details
    interviewer_name = Column(String)
    interviewer_role = Column(String)
    interview_format = Column(String)  # phone, video, in-person, panel
    interview_notes = Column(Text)  # Pre-interview notes

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    application = relationship("Application", backref="interview_prep")


class PracticeQuestion(Base):
    """Store practice questions and answers for interview prep."""
    __tablename__ = "practice_questions"

    id = Column(Integer, primary_key=True)
    interview_prep_id = Column(Integer, ForeignKey("interview_prep.id"), nullable=False)

    # Question details
    question = Column(Text, nullable=False)
    question_type = Column(String)  # behavioral, technical, situational, company-specific
    difficulty = Column(String)  # easy, medium, hard

    # Answer
    prepared_answer = Column(Text)
    talking_points = Column(Text)  # JSON array of key points

    # Practice tracking
    times_practiced = Column(Integer, default=0)
    confidence_level = Column(Integer)  # 1-5 scale
    last_practiced = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    interview_prep = relationship("InterviewPrep", backref="questions")


class InterviewFeedback(Base):
    """Store post-interview feedback and reflections."""
    __tablename__ = "interview_feedback"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    # Interview details
    interview_date = Column(DateTime)
    interview_type = Column(String)  # phone_screen, technical, behavioral, final
    interviewer = Column(String)
    duration_minutes = Column(Integer)

    # Feedback
    went_well = Column(Text)  # What went well
    went_poorly = Column(Text)  # What could improve
    questions_asked = Column(Text)  # JSON array of questions asked
    questions_struggled = Column(Text)  # Questions you struggled with

    # Self-rating
    overall_rating = Column(Integer)  # 1-5 how well it went
    confidence_after = Column(Integer)  # 1-5 confidence level

    # Follow-up
    next_steps = Column(Text)  # What are the next steps
    follow_up_sent = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    application = relationship("Application", backref="interview_feedback")


# Helper functions

def _get_or_create_prep(db, application_id: int) -> InterviewPrep:
    """Get or create the prep row using the CALLER's session (keeps it attached)."""
    prep = db.query(InterviewPrep).filter(
        InterviewPrep.application_id == application_id
    ).first()
    if not prep:
        prep = InterviewPrep(application_id=application_id)
        db.add(prep)
        db.commit()
        db.refresh(prep)
    return prep


def get_or_create_interview_prep(application_id: int) -> InterviewPrep:
    """Get existing interview prep or create new one."""
    db = SessionLocal()
    try:
        return _get_or_create_prep(db, application_id)
    finally:
        db.close()


def update_interview_prep(
    application_id: int,
    company_research: str = None,
    company_culture: str = None,
    recent_news: str = None,
    key_skills: str = None,
    relevant_experience: str = None,
    interviewer_name: str = None,
    interviewer_role: str = None,
    interview_format: str = None,
    interview_notes: str = None
) -> InterviewPrep:
    """Update interview prep data."""
    db = SessionLocal()
    try:
        # Use THIS session for get-or-create — previously this called the public
        # helper, which used (and closed) its own session, returning a detached
        # object whose edits were never persisted by the commit below.
        prep = _get_or_create_prep(db, application_id)

        # Update provided fields
        if company_research is not None:
            prep.company_research = company_research
        if company_culture is not None:
            prep.company_culture = company_culture
        if recent_news is not None:
            prep.recent_news = recent_news
        if key_skills is not None:
            prep.key_skills = key_skills
        if relevant_experience is not None:
            prep.relevant_experience = relevant_experience
        if interviewer_name is not None:
            prep.interviewer_name = interviewer_name
        if interviewer_role is not None:
            prep.interviewer_role = interviewer_role
        if interview_format is not None:
            prep.interview_format = interview_format
        if interview_notes is not None:
            prep.interview_notes = interview_notes

        prep.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(prep)

        return prep
    finally:
        db.close()


def add_practice_question(
    interview_prep_id: int,
    question: str,
    question_type: str = "behavioral",
    difficulty: str = "medium",
    prepared_answer: str = "",
    talking_points: str = ""
) -> PracticeQuestion:
    """Add a practice question."""
    db = SessionLocal()
    try:
        q = PracticeQuestion(
            interview_prep_id=interview_prep_id,
            question=question,
            question_type=question_type,
            difficulty=difficulty,
            prepared_answer=prepared_answer,
            talking_points=talking_points
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        return q
    finally:
        db.close()


def update_practice_question(
    question_id: int,
    prepared_answer: str = None,
    talking_points: str = None,
    confidence_level: int = None
) -> PracticeQuestion:
    """Update a practice question."""
    db = SessionLocal()
    try:
        q = db.query(PracticeQuestion).filter(PracticeQuestion.id == question_id).first()
        if not q:
            return None

        if prepared_answer is not None:
            q.prepared_answer = prepared_answer
        if talking_points is not None:
            q.talking_points = talking_points
        if confidence_level is not None:
            q.confidence_level = confidence_level

        q.times_practiced += 1
        q.last_practiced = datetime.utcnow()

        db.commit()
        db.refresh(q)
        return q
    finally:
        db.close()


def get_practice_questions(interview_prep_id: int) -> list:
    """Get all practice questions for interview prep."""
    db = SessionLocal()
    try:
        questions = db.query(PracticeQuestion).filter(
            PracticeQuestion.interview_prep_id == interview_prep_id
        ).order_by(PracticeQuestion.created_at).all()
        return questions
    finally:
        db.close()


def add_interview_feedback(
    application_id: int,
    interview_date: datetime,
    interview_type: str,
    interviewer: str = "",
    duration_minutes: int = 60,
    went_well: str = "",
    went_poorly: str = "",
    questions_asked: str = "",
    questions_struggled: str = "",
    overall_rating: int = 3,
    confidence_after: int = 3,
    next_steps: str = ""
) -> InterviewFeedback:
    """Add interview feedback after completing an interview."""
    db = SessionLocal()
    try:
        feedback = InterviewFeedback(
            application_id=application_id,
            interview_date=interview_date,
            interview_type=interview_type,
            interviewer=interviewer,
            duration_minutes=duration_minutes,
            went_well=went_well,
            went_poorly=went_poorly,
            questions_asked=questions_asked,
            questions_struggled=questions_struggled,
            overall_rating=overall_rating,
            confidence_after=confidence_after,
            next_steps=next_steps
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    finally:
        db.close()


def get_interview_feedback(application_id: int) -> list:
    """Get all interview feedback for an application."""
    db = SessionLocal()
    try:
        feedback = db.query(InterviewFeedback).filter(
            InterviewFeedback.application_id == application_id
        ).order_by(InterviewFeedback.interview_date.desc()).all()
        return feedback
    finally:
        db.close()


# Common interview questions by category

COMMON_QUESTIONS = {
    "behavioral": [
        "Tell me about yourself",
        "Why do you want to work here?",
        "What are your greatest strengths?",
        "What is your greatest weakness?",
        "Tell me about a time you failed",
        "Describe a challenging situation and how you handled it",
        "Tell me about a time you worked with a difficult person",
        "What motivates you?",
        "Where do you see yourself in 5 years?",
        "Why are you leaving your current role?",
    ],
    "technical": [
        "Walk me through your technical background",
        "Describe a complex technical problem you solved",
        "How do you stay current with technology?",
        "Explain [specific technology] to a non-technical person",
        "What's your experience with [specific tool/framework]?",
        "How do you approach debugging?",
        "Describe your development process",
        "What's the most challenging technical project you've worked on?",
    ],
    "sales_engineer": [
        "How do you handle technical objections from customers?",
        "Describe your approach to a technical demo",
        "How do you explain complex technical concepts to non-technical buyers?",
        "Tell me about a deal you helped close",
        "How do you collaborate with sales teams?",
        "What's your experience with POCs?",
        "How do you stay technical while in a customer-facing role?",
    ],
    "solution_architect": [
        "Describe your approach to solution design",
        "How do you gather requirements from stakeholders?",
        "Walk me through a complex architecture you designed",
        "How do you balance technical excellence with business needs?",
        "Describe your experience with cloud architectures",
        "How do you ensure scalability and reliability?",
    ],
    "questions_to_ask": [
        "What does success look like in this role after 6 months?",
        "What are the biggest challenges facing the team right now?",
        "How does this role contribute to company goals?",
        "What is the team structure and who would I work with?",
        "What opportunities are there for growth and learning?",
        "What's the onboarding process like?",
        "How does the company support professional development?",
        "What do you enjoy most about working here?",
    ]
}


def get_common_questions(category: str = "behavioral") -> list:
    """Get common interview questions by category."""
    return COMMON_QUESTIONS.get(category, [])
