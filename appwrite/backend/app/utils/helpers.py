"""Small reusable helpers for the modular backend."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import jsonify, request, session


def json_ok(**payload):
    payload.setdefault("success", True)
    return jsonify(payload)


def json_error(message, status=400, **payload):
    body = {"success": False, "error": message}
    body.update(payload)
    return jsonify(body), status


def get_request_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict(flat=True) if request.form else {}


def normalize_email(value):
    return (value or "").strip().lower()


def normalize_text(value, default=""):
    value = (value or "").strip()
    return value or default


def parse_limit(value, default=25, minimum=1, maximum=100):
    try:
        limit = int(value)
    except Exception:
        limit = default
    return max(minimum, min(limit, maximum))


def utc_now():
    return datetime.now(timezone.utc)


def session_user_email():
    return normalize_email(session.get("user"))


def row_to_dict(row):
    if not row:
        return None
    return {key: row[key] for key in row.keys()}

