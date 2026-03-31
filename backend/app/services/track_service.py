"""Track and project service helpers."""

from __future__ import annotations

from backend.app.extensions import db
from backend.app.models.project import Project
from backend.app.models.track import Track
from backend.app.schemas.track_schema import TrackSchema
from backend.app.utils.helpers import normalize_text, parse_limit


track_schema = TrackSchema()

BUILTIN_TRACKS = [
    {
        "title": "Clap Ritual",
        "artist": "CYBERGHOST",
        "source_url": "/assets/audio/clap_sound.mp3",
        "category": "sample",
        "duration_seconds": None,
        "notes": "Legacy clap sample asset",
    },
    {
        "title": "Ghost Noise",
        "artist": "CYBERGHOST",
        "source_url": "/assets/audio/audio.wav",
        "category": "sample",
        "duration_seconds": None,
        "notes": "Legacy noise sample asset",
    },
    {
        "title": "Preview Loop",
        "artist": "CYBERGHOST",
        "source_url": "/assets/video/preview.mp4",
        "category": "preview",
        "duration_seconds": None,
        "notes": "Original preview media asset",
    },
]


def list_builtin_tracks():
    return [dict(item) for item in BUILTIN_TRACKS]


def _tracks_from_db(limit):
    rows = Track.query.order_by(Track.id.desc()).limit(limit).all()
    return [track_schema.dump(row) for row in rows]


def list_tracks(limit=50):
    limit = parse_limit(limit, default=50, maximum=200)
    builtin = list_builtin_tracks()
    items = _tracks_from_db(limit)
    seen = {item["source_url"] for item in items if item.get("source_url")}
    for item in builtin:
        if item["source_url"] not in seen:
            items.append(item)
    return items[:limit]


def get_track(track_id):
    row = Track.query.get(track_id)
    if not row:
        return None
    return track_schema.dump(row)


def create_track(payload):
    payload = payload or {}
    title = normalize_text(payload.get("title"), "Untitled Track")
    source_url = normalize_text(payload.get("source_url"))
    if not source_url:
        return {"success": False, "error": "source_url required", "status_code": 400}

    track = Track(
        title=title,
        artist=normalize_text(payload.get("artist"), "Unknown Artist"),
        source_url=source_url,
        category=normalize_text(payload.get("category"), "library"),
        duration_seconds=payload.get("duration_seconds"),
        notes=normalize_text(payload.get("notes"), ""),
    )
    db.session.add(track)
    db.session.commit()
    return {"success": True, "track": track_schema.dump(track), "status_code": 201}


def list_projects(limit=25):
    limit = parse_limit(limit, default=25, maximum=100)
    rows = Project.query.order_by(Project.id.desc()).limit(limit).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "owner_email": row.owner_email or "",
            "description": row.description or "",
            "status": row.status or "draft",
            "created_at": str(row.created_at) if row.created_at else None,
        }
        for row in rows
    ]


def get_project(project_id):
    row = Project.query.get(project_id)
    if not row:
        return None
    return {
        "id": row.id,
        "name": row.name,
        "owner_email": row.owner_email or "",
        "description": row.description or "",
        "status": row.status or "draft",
        "created_at": str(row.created_at) if row.created_at else None,
    }


def create_project(payload):
    payload = payload or {}
    name = normalize_text(payload.get("name"))
    if not name:
        return {"success": False, "error": "name required", "status_code": 400}

    project = Project(
        name=name,
        owner_email=normalize_text(payload.get("owner_email"), ""),
        description=normalize_text(payload.get("description"), ""),
        status=normalize_text(payload.get("status"), "draft"),
    )
    db.session.add(project)
    db.session.commit()
    return {"success": True, "project": get_project(project.id), "status_code": 201}

