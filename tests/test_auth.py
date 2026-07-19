"""Tests for auth (hashing) and multi-tenant user data isolation."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core import auth
from db import users
from db.models import Base


@pytest.fixture
def db():
    """A fresh in-memory database for each test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


class TestPasswordHashing:
    def test_hash_verify_roundtrip(self):
        h = auth.hash_password("correct horse battery staple")
        assert auth.verify_password("correct horse battery staple", h)

    def test_wrong_password_fails(self):
        h = auth.hash_password("secret123")
        assert not auth.verify_password("wrong", h)

    def test_hashes_are_salted(self):
        assert auth.hash_password("same") != auth.hash_password("same")

    def test_garbage_stored_hash_is_false(self):
        assert not auth.verify_password("x", "not-a-real-hash")

    def test_validate_credentials(self):
        assert auth.validate_credentials("bad-email", "longenough") is not None
        assert auth.validate_credentials("a@b.com", "short") is not None
        assert auth.validate_credentials("a@b.com", "longenough1") is None


class TestUserAccounts:
    def test_create_and_authenticate(self, db):
        users.create_user(db, "Alex@Example.com", "password123")
        # email is normalized to lowercase
        assert users.authenticate(db, "alex@example.com", "password123") is not None
        assert users.authenticate(db, "alex@example.com", "wrong") is None

    def test_duplicate_email_rejected(self, db):
        users.create_user(db, "dup@example.com", "password123")
        with pytest.raises(users.EmailAlreadyExists):
            users.create_user(db, "dup@example.com", "password123")


class TestDataIsolation:
    def test_users_cannot_see_each_others_applications(self, db):
        alice = users.create_user(db, "alice@example.com", "password123")
        bob = users.create_user(db, "bob@example.com", "password123")

        users.add_application(db, alice.id, company="Acme", role="Data Scientist")
        users.add_application(db, bob.id, company="Globex", role="ML Engineer")

        alice_apps = users.list_applications(db, alice.id)
        bob_apps = users.list_applications(db, bob.id)

        assert [a.company for a in alice_apps] == ["Acme"]
        assert [a.company for a in bob_apps] == ["Globex"]

    def test_cannot_fetch_another_users_application_by_id(self, db):
        alice = users.create_user(db, "alice@example.com", "password123")
        bob = users.create_user(db, "bob@example.com", "password123")
        app = users.add_application(db, alice.id, company="Acme", role="DS")

        # Bob tries to fetch Alice's application by id -> denied
        assert users.get_application(db, bob.id, app.id) is None
        assert users.get_application(db, alice.id, app.id) is not None
