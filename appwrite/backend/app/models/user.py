"""SQLAlchemy model for backend users."""

from __future__ import annotations

from backend.app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text)
    role = db.Column(db.Text, default="user")
    is_active = db.Column(db.Integer, default=1)
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.Integer)

