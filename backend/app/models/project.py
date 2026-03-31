"""SQLAlchemy model for music projects."""

from __future__ import annotations

from backend.app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    owner_email = db.Column(db.Text)
    description = db.Column(db.Text)
    status = db.Column(db.Text, default="draft")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

