"""Lightweight automatic contact search helpers.

The original root-level CLI expected a richer search helper.  This version keeps
the interface intact while searching the local contacts database using the
available contact metadata.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

APPWRITE_ROOT = Path(__file__).resolve().parents[3]
if str(APPWRITE_ROOT) not in sys.path:
    sys.path.insert(0, str(APPWRITE_ROOT))

from kernel.bridge.python_engine.database_manager import DatabaseManager
from kernel.bridge.python_engine.email_extractor import EmailValidator


class AutoEmailExtractor:
    """Search stored contacts using simple text filters."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "./database/devnav.db")
        self.manager = DatabaseManager(self.db_path)
        self.validator = EmailValidator(
            enable_virus_check=os.getenv("ENABLE_VIRUS_CHECK", "true").lower() == "true",
            enable_source_verification=os.getenv("ENABLE_SOURCE_VERIFICATION", "true").lower() == "true",
        )

    @staticmethod
    def _normalize_list(value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            items = value.split(",")
        else:
            try:
                items = list(value)  # type: ignore[arg-type]
            except TypeError:
                items = [str(value)]
        return [item.strip().lower() for item in items if str(item).strip()]

    def _load_contacts(self) -> List[Dict[str, object]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email, name, title, company, department, country, source, created_at
            FROM contacts
            WHERE archived = 0
            ORDER BY datetime(created_at) DESC, email ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        contacts: List[Dict[str, object]] = []
        for row in rows:
            contacts.append(
                {
                    "id": row[0],
                    "email": row[1],
                    "name": row[2] or "",
                    "title": row[3] or "",
                    "company": row[4] or "",
                    "department": row[5] or "",
                    "country": row[6] or "",
                    "source": row[7] or "",
                    "created_at": row[8],
                }
            )
        return contacts

    def _contact_text(self, contact: Dict[str, object]) -> str:
        pieces = [
            contact.get("email", ""),
            contact.get("name", ""),
            contact.get("title", ""),
            contact.get("company", ""),
            contact.get("department", ""),
            contact.get("country", ""),
            contact.get("source", ""),
        ]
        return " ".join(str(piece) for piece in pieces).lower()

    def _matches(self, contact: Dict[str, object], criteria: Dict[str, object]) -> bool:
        haystack = self._contact_text(contact)

        title = str(criteria.get("title") or "").strip().lower()
        if title:
            title_terms = [term for term in title.split() if term]
            if title not in haystack and not any(term in haystack for term in title_terms):
                return False

        keywords = self._normalize_list(criteria.get("keywords"))
        if keywords and not any(keyword in haystack for keyword in keywords):
            return False

        country = str(criteria.get("country") or "").strip().lower()
        if country and country != str(contact.get("country") or "").strip().lower():
            return False

        if bool(criteria.get("remote")):
            remote_terms = ("remote", "work from home", "wfh", "telecommute")
            if not any(term in haystack for term in remote_terms):
                return False

        email = str(contact.get("email") or "").strip().lower()
        is_valid, _ = self.validator.is_valid_email(email)
        if not is_valid:
            return False

        return True

    def search_with_filters(self, criteria: Dict[str, object]) -> List[Dict[str, object]]:
        """Return contacts that match the supplied criteria."""
        results: List[Dict[str, object]] = []
        for contact in self._load_contacts():
            if self._matches(contact, criteria):
                results.append(contact)
        return results

    def search_all_sources(self, criteria: Dict[str, object], limit: int = 100) -> Tuple[int, List[Dict[str, object]]]:
        """Return matches from all available local sources.

        The historical CLI expected a stored-count and a result list. We keep the
        same shape, but the current implementation searches the local contacts
        store instead of remote sources.
        """
        results = self.search_with_filters(criteria)
        try:
            limit_value = max(0, int(limit))
        except Exception:
            limit_value = 100
        return len(results[:limit_value]), results[:limit_value]
