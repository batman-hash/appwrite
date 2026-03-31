"""Authentication API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify

from backend.app.services.auth_service import (
    activate_user,
    authenticate_user,
    current_user_payload,
    logout_user,
    register_user,
    request_password_reset,
)
from backend.app.utils.helpers import get_request_payload


auth_bp = Blueprint("modular_auth", __name__, url_prefix="/api/auth")


def _json_result(result):
    status_code = int(result.get("status_code", 200)) if isinstance(result, dict) else 200
    payload = dict(result or {})
    payload.pop("status_code", None)
    return jsonify(payload), status_code


@auth_bp.get("/me")
def me():
    user = current_user_payload()
    if not user:
        return jsonify(success=False, error="Unauthorized"), 401
    return jsonify(success=True, user=user)


@auth_bp.post("/login")
def login():
    payload = get_request_payload()
    return _json_result(authenticate_user(payload.get("email"), payload.get("password")))


@auth_bp.post("/register")
def register():
    payload = get_request_payload()
    return _json_result(
        register_user(
            payload.get("username"),
            payload.get("email"),
            payload.get("password"),
            role=payload.get("role") or "user",
        )
    )


@auth_bp.post("/request-reset")
def request_reset():
    payload = get_request_payload()
    return _json_result(request_password_reset(payload.get("email")))


@auth_bp.get("/activate/<token>")
@auth_bp.post("/activate")
def activate(token=None):
    payload = get_request_payload()
    token = token or payload.get("token")
    return _json_result(activate_user(token))


@auth_bp.post("/logout")
@auth_bp.get("/logout")
def logout():
    return _json_result(logout_user())
