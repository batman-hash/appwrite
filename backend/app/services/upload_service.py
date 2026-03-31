"""Upload and shared-file helpers."""

from __future__ import annotations

import base64

from backend.app.extensions import conn
from backend.app.utils.helpers import parse_limit, row_to_dict
from backend.app.utils.validators import is_email


def _row_payload(row):
    if not row:
        return None
    data = row_to_dict(row)
    return {
        "id": data.get("id"),
        "file_name": data.get("file_name", ""),
        "image_data": data.get("image_data", ""),
        "uploader_email": data.get("uploader_email", "") or "",
        "created_at": data.get("created_at"),
    }


def list_shared_files(limit=24):
    limit = parse_limit(limit, default=24, maximum=100)
    with conn() as db:
        rows = db.execute(
            """
            SELECT id, file_name, image_data, uploader_email, created_at
            FROM shared_files
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_payload(row) for row in rows]


def create_shared_file(file_name, image_data, uploader_email=""):
    file_name = (file_name or "poster.png").strip()[:120]
    image_data = (image_data or "").strip()
    uploader_email = (uploader_email or "").strip().lower()

    if not image_data.startswith("data:image/"):
        return {"success": False, "error": "Invalid image payload", "status_code": 400}
    if len(image_data.encode("utf-8", errors="ignore")) > 2_500_000:
        return {"success": False, "error": "Image too large", "status_code": 413}
    if uploader_email and not is_email(uploader_email):
        return {"success": False, "error": "Invalid uploader email", "status_code": 400}

    with conn() as db:
        cur = db.execute(
            "INSERT INTO shared_files(file_name,image_data,uploader_email) VALUES(?,?,?)",
            (file_name, image_data, uploader_email or None),
        )
        db.commit()
        row = db.execute(
            "SELECT id, file_name, image_data, uploader_email, created_at FROM shared_files WHERE id=?",
            (cur.lastrowid,),
        ).fetchone()

    return {"success": True, "item": _row_payload(row), "status_code": 201}


def create_shared_file_from_upload(file_storage, uploader_email=""):
    if not file_storage:
        return {"success": False, "error": "File required", "status_code": 400}

    mimetype = (getattr(file_storage, "mimetype", "") or "").lower()
    if not mimetype.startswith("image/"):
        return {"success": False, "error": "Only image uploads are supported", "status_code": 400}

    payload = file_storage.read() or b""
    encoded = base64.b64encode(payload).decode("ascii")
    image_data = f"data:{mimetype};base64,{encoded}"
    return create_shared_file(getattr(file_storage, "filename", "upload.png"), image_data, uploader_email=uploader_email)

