"""Modular Flask facade layered on top of the legacy backend app."""

from __future__ import annotations

import os

from backend import webapp as legacy
from backend.app.config import Config
from backend.app.extensions import db
from backend.app.routes.auth import auth_bp
from backend.app.routes.users import users_bp
from backend.app.routes.tracks import tracks_bp
from backend.app.routes.uploads import uploads_bp


_REGISTERED = False


def _apply_config(app):
    app.config.from_object(Config)
    app.config.setdefault("JSON_SORT_KEYS", False)
    app.config.setdefault("JSONIFY_PRETTYPRINT_REGULAR", False)
    return app


def _register_blueprints(app):
    global _REGISTERED
    if _REGISTERED:
        return app

    for blueprint in (auth_bp, users_bp, tracks_bp, uploads_bp):
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)

    _REGISTERED = True
    return app


def create_app():
    """Return the shared Flask app with the modular blueprints attached."""

    app = legacy.app
    _apply_config(app)
    _register_blueprints(app)

    try:
        os.makedirs(legacy.CONFIG_DIR, exist_ok=True)
        if legacy.REQUEST_OBS_PATH and not os.path.exists(legacy.REQUEST_OBS_PATH):
            with open(legacy.REQUEST_OBS_PATH, "w", encoding="utf-8") as handle:
                handle.write("[]")
    except Exception:
        pass

    with app.app_context():
        try:
            legacy.init_db()
        except Exception:
            pass
        db.create_all()

    return app


app = create_app()
