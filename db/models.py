from sqlalchemy import Column, Integer, String, Date, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """A registered user (multi-user / friends-beta)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="user")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    # Owner (nullable so pre-existing single-user rows still load).
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    company = Column(String, nullable=False)
    role = Column(String)
    job_url = Column(String)                    # URL to job posting
    job_description = Column(Text)              # Full job description text
    status = Column(String, default="Draft")    # Draft, Applied, Interview, etc.
    application_date = Column(DateTime)         # When applied
    created_at = Column(DateTime, default=datetime.utcnow)  # When record created

    # Fit Analysis (saved)
    fit_score = Column(Float)                   # 1-10 score
    fit_analysis_json = Column(Text)            # JSON: matched skills, gaps, recommendation
    role_category = Column(String)              # sales_engineer, solution_architect, etc.
    seniority_level = Column(String)            # junior, mid, senior

    # Generated Content (saved)
    cover_letter_text = Column(Text)            # Full generated cover letter
    cv_suggestions = Column(Text)               # Suggestions for CV customization

    # Legacy/other fields
    cv_used = Column(String)                    # Which CV version used
    cover_letter = Column(String)               # Legacy: file path
    last_contact = Column(Date)                 # For follow-ups
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="applications")
    history = relationship("ApplicationHistory", back_populates="application", order_by="ApplicationHistory.created_at.desc()")


class ApplicationHistory(Base):
    """Track all changes and events for an application."""
    __tablename__ = "application_history"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event_type = Column(String)      # status_change, note_added, cover_letter_generated, etc.
    old_value = Column(String)       # Previous status/value
    new_value = Column(String)       # New status/value
    details = Column(Text)           # Additional details/notes

    application = relationship("Application", back_populates="history")


class JobPosting(Base):
    """A job posting discovered by the target-company watcher (Greenhouse/Lever)."""
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True)
    company = Column(String, nullable=False)          # display name (from TargetCompany)
    source = Column(String, nullable=False)           # greenhouse | lever
    external_id = Column(String, nullable=False, index=True)  # posting id on the board
    title = Column(String, nullable=False)
    location = Column(String)
    url = Column(String)
    description = Column(Text)                        # plain-text excerpt for fit scoring

    fit_score = Column(Float)                         # local fit vs. CV at discovery time
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)            # 0 once it disappears from the board
    dismissed = Column(Integer, default=0)            # user hid it


class EmailAnalysis(Base):
    """Store LLM analysis of application-related emails."""
    __tablename__ = "email_analyses"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)

    # Email identification
    email_id = Column(String)                     # Gmail message ID
    subject = Column(String)                      # Email subject
    sender = Column(String)                       # From address
    received_date = Column(DateTime)              # When email was received

    # Analysis results
    email_type = Column(String)                   # rejection, interview_invite, offer, scheduling, etc.
    confidence = Column(Float)                    # 0-1 confidence score
    summary = Column(Text)                        # One sentence summary

    # Extracted information
    extracted_date = Column(String)               # YYYY-MM-DD or null
    extracted_time = Column(String)               # HH:MM or null
    next_steps = Column(Text)                     # JSON array of action items
    suggested_status = Column(String)             # Suggested status update

    # Key details as JSON
    key_details = Column(Text)                    # JSON: interviewer_name, format, location, deadline

    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analysis_provider = Column(String)            # groq, google, local, etc.

    # Relationship
    application = relationship("Application", backref="email_analyses")

