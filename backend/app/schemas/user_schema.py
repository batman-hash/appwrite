"""Serialization helpers for users."""

from __future__ import annotations

from backend.app.utils.helpers import row_to_dict


class UserSchema:
    def dump(self, obj):
        if obj is None:
            return None
        if hasattr(obj, "__table__"):
            return {
                "id": getattr(obj, "id", None),
                "email": getattr(obj, "email", ""),
                "username": getattr(obj, "username", "") or "",
                "role": getattr(obj, "role", "user") or "user",
                "is_active": getattr(obj, "is_active", 1),
            }
        if hasattr(obj, "keys"):
            data = row_to_dict(obj)
            return {
                "id": data.get("id"),
                "email": data.get("email", ""),
                "username": data.get("username", "") or "",
                "role": data.get("role", "user") or "user",
                "is_active": data.get("is_active", 1),
            }
        return None

