"""Track and project API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.app.middleware.auth_middleware import require_login
from backend.app.services.track_service import (
    create_project,
    create_track,
    get_project,
    get_track,
    list_builtin_tracks,
    list_projects,
    list_tracks,
)
from backend.app.utils.helpers import get_request_payload, parse_limit


tracks_bp = Blueprint("modular_tracks", __name__, url_prefix="/api/tracks")


def _json_result(result):
    status_code = int(result.get("status_code", 200)) if isinstance(result, dict) else 200
    payload = dict(result or {})
    payload.pop("status_code", None)
    return jsonify(payload), status_code


@tracks_bp.get("")
@tracks_bp.get("/")
def tracks():
    limit = parse_limit(request.args.get("limit", "50"), default=50, maximum=200)
    return jsonify(success=True, items=list_tracks(limit))


@tracks_bp.get("/library")
def library():
    return jsonify(success=True, items=list_builtin_tracks())


@tracks_bp.post("")
@tracks_bp.post("/")
@require_login
def create():
    return _json_result(create_track(get_request_payload()))


@tracks_bp.get("/<int:track_id>")
def track(track_id):
    row = get_track(track_id)
    if not row:
        return jsonify(success=False, error="Track not found"), 404
    return jsonify(success=True, track=row)


@tracks_bp.get("/projects")
def projects():
    limit = parse_limit(request.args.get("limit", "25"), default=25, maximum=100)
    return jsonify(success=True, items=list_projects(limit))


@tracks_bp.get("/projects/<int:project_id>")
def project(project_id):
    row = get_project(project_id)
    if not row:
        return jsonify(success=False, error="Project not found"), 404
    return jsonify(success=True, project=row)


@tracks_bp.post("/projects")
@require_login
def create_project_route():
    return _json_result(create_project(get_request_payload()))

