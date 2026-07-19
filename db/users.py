"""
User accounts + per-user data access.

Every application query is scoped by ``user_id`` — this is the multi-tenant isolation
guarantee: one user can never see or touch another user's data. Functions take an explicit
SQLAlchemy ``Session`` so they are easy to unit-test against a throwaway database.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from core.auth import hash_password, verify_password
from db.models import Application, User


class EmailAlreadyExists(Exception):
    """Raised when registering an email that is already taken."""


# --- accounts ---------------------------------------------------------------------

def create_user(db: Session, email: str, password: str) -> User:
    """Register a new user. Raises EmailAlreadyExists if the email is taken."""
    email = email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise EmailAlreadyExists(email)
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    """Return the User if email+password are valid, else None."""
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


# --- per-user applications (always scoped by user_id) -----------------------------

def list_applications(db: Session, user_id: int) -> List[Application]:
    return (
        db.query(Application)
        .filter(Application.user_id == user_id)
        .order_by(Application.id.desc())
        .all()
    )


def add_application(db: Session, user_id: int, **fields) -> Application:
    app = Application(user_id=user_id, **fields)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def get_application(db: Session, user_id: int, app_id: int) -> Optional[Application]:
    """Fetch one application, but only if it belongs to *user_id*."""
    return (
        db.query(Application)
        .filter(Application.id == app_id, Application.user_id == user_id)
        .first()
    )
