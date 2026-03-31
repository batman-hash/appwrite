"""Auth-related service functions."""

from __future__ import annotations

import sqlite3

import bcrypt
from flask import session

from backend import webapp as legacy
from backend.app.extensions import conn
from backend.app.schemas.user_schema import UserSchema
from backend.app.utils.helpers import normalize_email
from backend.app.utils.security import hash_password, verify_password
from backend.app.utils.validators import is_email, require_fields


user_schema = UserSchema()


def _user_row(email):
    with conn() as db:
        return db.execute(
            """
            SELECT id, email, username, role, is_active, failed_login_count, locked_until, password
            FROM users
            WHERE email=?
            """,
            (email,),
        ).fetchone()


def current_user_payload():
    email = normalize_email(session.get("user"))
    if not email:
        return None
    row = _user_row(email)
    if not row:
        return None
    payload = user_schema.dump(row)
    payload["email"] = email
    return payload


def authenticate_user(email, password):
    email = normalize_email(email)
    if not email or not password:
        return {"success": False, "error": "Missing email or password", "status_code": 400}

    row = _user_row(email)
    if not row:
        return {"success": False, "error": "Invalid email or password", "status_code": 401}

    if legacy._is_user_locked(row):
        return {"success": False, "error": legacy._lock_message(), "status_code": 423}

    if not verify_password(password, row["password"]):
        failed = legacy._register_failed_login_attempt(row)
        if failed.get("locked"):
            return {"success": False, "error": legacy._lock_message(), "status_code": 423}
        return {"success": False, "error": "Invalid email or password", "status_code": 401}

    if int(row["is_active"] or 0) == 0:
        return {"success": False, "error": "Account not activated", "status_code": 403}

    legacy._reset_failed_login_state(email)
    session["user"] = email
    session["chat_user"] = email
    payload = user_schema.dump(row)
    payload["email"] = email
    payload["username"] = payload.get("username") or email
    return {"success": True, "user": payload, "status_code": 200}


def register_user(username, email, password, role="user"):
    missing = require_fields({"username": username, "email": email, "password": password}, "username", "email", "password")
    if missing:
        return {"success": False, "error": f"Missing fields: {', '.join(missing)}", "status_code": 400}
    email = normalize_email(email)
    if not is_email(email):
        return {"success": False, "error": "Invalid email", "status_code": 400}

    hashed = hash_password(password)
    try:
        with conn() as db:
            db.execute(
                """
                INSERT INTO users(username, email, password, role, is_active, failed_login_count, locked_until)
                VALUES (?, ?, ?, ?, 0, 0, NULL)
                """,
                (username.strip(), email, hashed, role or "user"),
            )
            db.commit()
    except sqlite3.IntegrityError:
        resent = legacy._resend_activation_if_inactive(email, username_fallback=username)
        if resent:
            return {"success": True, "message": "Activation email resent", "status_code": 200}
        return {"success": False, "error": "Email already exists", "status_code": 409}

    legacy._registration_email_workflow(username.strip(), email)
    return {"success": True, "message": "Registration successful", "status_code": 200}


def request_password_reset(email):
    email = normalize_email(email)
    return legacy.create_reset_request(email)


def activate_user(token):
    if not token:
        return {"success": False, "error": "Token required", "status_code": 400}
    ok = legacy._activate_account_by_token(token.strip())
    if not ok:
        return {"success": False, "error": "Invalid or expired token", "status_code": 400}
    return {"success": True, "message": "Account activated", "status_code": 200}


def logout_user():
    chat_email = normalize_email(session.get("chat_user"))
    session.clear()
    try:
        if chat_email:
            legacy.ACTIVE_CHAT_USERS.pop(chat_email, None)
    except Exception:
        pass
    return {"success": True, "message": "Logged out", "status_code": 200}
