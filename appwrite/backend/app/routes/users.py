"""User management API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.middleware.auth_middleware import require_login
from backend.app.services.auth_service import current_user_payload
from backend.app.services.user_service import (
    get_user_email_history,
    list_recent_users,
    send_user_email,
    sync_users_to_subscribers,
)
from backend.app.utils.helpers import get_request_payload, parse_limit


users_bp = Blueprint("modular_users", __name__, url_prefix="/api/users")


def _json_result(result):
    status_code = int(result.get("status_code", 200)) if isinstance(result, dict) else 200
    payload = dict(result or {})
    payload.pop("status_code", None)
    return jsonify(payload), status_code


@users_bp.get("/me")
def me():
    user = current_user_payload()
    if not user:
        return jsonify(success=False, error="Unauthorized"), 401
    return jsonify(success=True, user=user)


@users_bp.get("")
@users_bp.get("/")
@require_login
def list_users():
    limit = parse_limit(request.args.get("limit", "25"), default=25, maximum=200)
    return jsonify(success=True, items=list_recent_users(limit))


@users_bp.post("/email/send")
@require_login
def email_send():
    payload = get_request_payload()
    return _json_result(
        send_user_email(
            payload.get("to_email"),
            payload.get("subject"),
            payload.get("body"),
        )
    )


@users_bp.get("/email/history")
@require_login
def email_history():
    result = get_user_email_history(request.args.get("limit", "50"))
    return _json_result(result)


@users_bp.post("/newsletter/sync")
@require_login
def newsletter_sync():
    result = sync_users_to_subscribers()
    return jsonify(success=True, **result)

