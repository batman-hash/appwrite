"""Security helpers for password hashing and token handling."""

from __future__ import annotations

import bcrypt
import hashlib
import hmac
import secrets


def hash_password(password):
    return bcrypt.hashpw((password or "").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed):
    if not password or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def new_token(length=32):
    return secrets.token_urlsafe(length)


def hash_token(token, pepper):
    return hashlib.sha256(f"{pepper}:{token}".encode("utf-8")).hexdigest()


def token_matches(candidate, token):
    return hmac.compare_digest(candidate or "", token or "")

