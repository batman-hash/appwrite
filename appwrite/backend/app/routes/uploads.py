"""Upload and shared-file API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from backend.app.services.upload_service import (
    create_shared_file,
    create_shared_file_from_upload,
    list_shared_files,
)
from backend.app.utils.helpers import get_request_payload, parse_limit, normalize_email


uploads_bp = Blueprint("modular_uploads", __name__, url_prefix="/api/uploads")


def _json_result(result):
    status_code = int(result.get("status_code", 200)) if isinstance(result, dict) else 200
    payload = dict(result or {})
    payload.pop("status_code", None)
    return jsonify(payload), status_code


@uploads_bp.get("/shared-files")
def shared_files():
    limit = parse_limit(request.args.get("limit", "24"), default=24, maximum=100)
    return jsonify(success=True, items=list_shared_files(limit))


@uploads_bp.post("/shared-files")
@uploads_bp.post("/image")
def upload_shared_file():
    uploader_email = normalize_email(
        request.form.get("uploader_email")
        or get_request_payload().get("uploader_email")
        or session.get("user")
        or session.get("chat_user")
    )

    if request.files:
        file_storage = request.files.get("file") or next(iter(request.files.values()))
        return _json_result(create_shared_file_from_upload(file_storage, uploader_email=uploader_email))

    payload = get_request_payload()
    file_name = payload.get("file_name") or payload.get("name") or "poster.png"
    image_data = payload.get("image_data") or payload.get("data")
    if not image_data and payload.get("base64"):
        mime = payload.get("mime") or "image/png"
        image_data = f"data:{mime};base64,{payload.get('base64')}"
    return _json_result(create_shared_file(file_name, image_data, uploader_email=uploader_email))
