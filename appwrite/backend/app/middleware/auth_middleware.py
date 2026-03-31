"""Authentication decorators for API routes."""

from __future__ import annotations

from functools import wraps

from flask import jsonify, session


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return jsonify(success=False, error="Unauthorized"), 401
        return fn(*args, **kwargs)

    return wrapper

