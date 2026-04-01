"""Template manager helpers for the relocated DevNavigator scripts."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

APPWRITE_ROOT = Path(__file__).resolve().parents[3]
if str(APPWRITE_ROOT) not in sys.path:
    sys.path.insert(0, str(APPWRITE_ROOT))

from kernel.bridge.send_test_emails import EmailTemplateManager as _EmailTemplateManager


class TemplateManager(_EmailTemplateManager):
    """Compat wrapper that exposes the template-listing helpers DevNavigator expects."""

    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path=db_path or os.getenv("DATABASE_PATH", "./database/devnav.db"))

    def get_all_templates(self) -> List[Dict[str, object]]:
        """Return every template row as a list of dictionaries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, subject, body, is_default, created_at, updated_at
            FROM email_templates
            ORDER BY is_default DESC, name ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        templates: List[Dict[str, object]] = []
        for row in rows:
            templates.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "subject": row[2],
                    "body": row[3],
                    "is_default": bool(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6],
                }
            )
        return templates
