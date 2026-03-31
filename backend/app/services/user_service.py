"""User and newsletter service helpers."""

from __future__ import annotations

from flask import session
from sqlalchemy import text

from backend import webapp as legacy
from backend.app.extensions import conn, db
from backend.app.utils.helpers import normalize_email, parse_limit, row_to_dict
from backend.app.utils.validators import is_email


def list_recent_users(limit=25):
    limit = parse_limit(limit, default=25, maximum=200)
    with conn() as db_conn:
        rows = db_conn.execute(
            """
            SELECT id, username, email, role, is_active, failed_login_count, locked_until
            FROM users
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_user_email_history(limit=50):
    limit = parse_limit(limit, default=50, maximum=200)
    user_email = normalize_email(session.get("user"))
    if not user_email:
        return {"success": False, "error": "Unauthorized", "status_code": 401}

    rows = (
        legacy.UserEmailMessageModel.query
        .filter_by(user_email=user_email)
        .order_by(legacy.UserEmailMessageModel.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": row.id,
            "to_email": row.to_email,
            "subject": row.subject,
            "status": row.status,
            "error": row.error,
            "created_at": str(row.created_at) if row.created_at else None,
            "sent_at": str(row.sent_at) if row.sent_at else None,
        }
        for row in rows
    ]
    return {"success": True, "items": items, "status_code": 200}


def send_user_email(to_email, subject, body):
    user_email = normalize_email(session.get("user"))
    if not user_email:
        return {"success": False, "error": "Unauthorized", "status_code": 401}
    if not is_email(to_email):
        return {"success": False, "error": "Invalid recipient email", "status_code": 400}
    if not subject or not body:
        return {"success": False, "error": "Missing fields", "status_code": 400}

    record = legacy.UserEmailMessageModel(
        user_email=user_email,
        to_email=normalize_email(to_email),
        subject=subject.strip(),
        body=body.strip(),
        status="pending",
    )
    db.session.add(record)
    db.session.commit()

    message_id = record.id
    email_sent = legacy.send_email(normalize_email(to_email), subject.strip(), f"<div style=\"font-family:Arial,sans-serif;\"><p>{body.strip().replace(chr(10), '<br>')}</p></div>")

    record = db.session.get(legacy.UserEmailMessageModel, message_id)
    if record:
        record.status = "sent" if email_sent else "failed"
        record.error = None if email_sent else "send_email returned False"
        if email_sent:
            db.session.execute(
                text("UPDATE user_email_messages SET sent_at=CURRENT_TIMESTAMP WHERE id=:id"),
                {"id": message_id},
            )
        db.session.commit()

    return {"success": True, "id": message_id, "status": "sent" if email_sent else "failed", "status_code": 200}


def sync_users_to_subscribers():
    return legacy._sync_users_to_subscribers()
