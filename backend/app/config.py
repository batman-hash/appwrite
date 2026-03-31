"""Config values for the modular backend wrapper."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DATABASE_PATH = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT))) / "user.db"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "dev-only-change-me"
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    FRONTEND_DIR = str(FRONTEND_ROOT)
    PROJECT_ROOT = str(PROJECT_ROOT)
    BACKEND_ROOT = str(BACKEND_ROOT)

