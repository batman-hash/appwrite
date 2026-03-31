"""Input validation helpers."""

from __future__ import annotations


def is_email(value):
    value = (value or "").strip()
    return bool(value and "@" in value and "." in value.rsplit("@", 1)[-1])


def require_fields(payload, *fields):
    missing = [field for field in fields if not (payload.get(field) or "").strip()]
    return missing


def sanitize_name(value, default="user"):
    value = (value or "").strip()
    return value or default

