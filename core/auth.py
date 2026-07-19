"""
Password hashing + validation (standard-library only — no bcrypt/passlib dependency).

Uses PBKDF2-HMAC-SHA256 with a per-password random salt. Stored format:
``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

_ITERATIONS = 200_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str, iterations: int = _ITERATIONS) -> str:
    """Hash a password with a fresh random salt."""
    if not password:
        raise ValueError("password must not be empty")
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash (constant-time compare)."""
    try:
        algo, iters, salt, hexhash = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(dk.hex(), hexhash)


def is_valid_email(email: str) -> bool:
    return bool(email) and _EMAIL_RE.match(email.strip()) is not None


def validate_credentials(email: str, password: str) -> str | None:
    """Return an error message if credentials are unacceptable, else None."""
    if not is_valid_email(email):
        return "Please enter a valid email address."
    if len(password or "") < 8:
        return "Password must be at least 8 characters."
    return None
