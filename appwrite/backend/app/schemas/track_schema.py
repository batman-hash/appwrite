"""Serialization helpers for tracks and projects."""

from __future__ import annotations

from backend.app.utils.helpers import row_to_dict


class TrackSchema:
    def dump(self, obj):
        if obj is None:
            return None
        if hasattr(obj, "__table__"):
            return {
                "id": getattr(obj, "id", None),
                "title": getattr(obj, "title", ""),
                "artist": getattr(obj, "artist", "") or "",
                "source_url": getattr(obj, "source_url", "") or "",
                "category": getattr(obj, "category", "library") or "library",
                "duration_seconds": getattr(obj, "duration_seconds", None),
                "notes": getattr(obj, "notes", "") or "",
            }
        if hasattr(obj, "keys"):
            data = row_to_dict(obj)
            return {
                "id": data.get("id"),
                "title": data.get("title", ""),
                "artist": data.get("artist", "") or "",
                "source_url": data.get("source_url", "") or "",
                "category": data.get("category", "library") or "library",
                "duration_seconds": data.get("duration_seconds"),
                "notes": data.get("notes", "") or "",
            }
        return None

