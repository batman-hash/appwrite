"""SQLAlchemy model for audio tracks and uploads."""

from __future__ import annotations

from backend.app.extensions import db


class Track(db.Model):
    __tablename__ = "tracks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    artist = db.Column(db.Text)
    source_url = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, default="library")
    duration_seconds = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

