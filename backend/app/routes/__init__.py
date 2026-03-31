"""Blueprint registration helpers for the modular backend."""

from backend.app.routes.auth import auth_bp
from backend.app.routes.tracks import tracks_bp
from backend.app.routes.uploads import uploads_bp
from backend.app.routes.users import users_bp

__all__ = ["auth_bp", "tracks_bp", "uploads_bp", "users_bp"]

