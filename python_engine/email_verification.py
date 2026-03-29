"""
Email verification workflow helpers.
"""
import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import quote

from python_engine.database_manager import DatabaseManager


DEFAULT_VERIFICATION_TEMPLATE = 'email_verification'


def get_email_verification_base_url() -> str:
    """Return the configured verification URL base, if any."""
    return os.getenv('EMAIL_VERIFICATION_BASE_URL', '').strip()


def build_verification_link(base_url: str, token: str) -> str:
    """Create a verification link from a configured base URL and token."""
    cleaned_base = (base_url or '').strip()
    if not cleaned_base:
        return '[SET EMAIL_VERIFICATION_BASE_URL]'

    separator = '&' if '?' in cleaned_base else '?'
    return f"{cleaned_base}{separator}token={quote(token)}"


@dataclass
class VerificationEmailPayload:
    """Context used to render and confirm a verification email."""

    email: str
    token: str
    verification_code: str
    expires_at: str
    verification_link: str
    template_name: str = DEFAULT_VERIFICATION_TEMPLATE
    request_id: Optional[int] = None
    contact_id: Optional[int] = None

    def to_template_context(self) -> Dict[str, str]:
        """Expose placeholders supported by the verification template."""
        return {
            'verification_link': self.verification_link,
            'verification_code': self.verification_code,
            'verification_expires_at': self.expires_at,
        }


class EmailVerificationService:
    """Create, track, and confirm email verification requests."""

    def __init__(self, db_path: Optional[str] = None):
        self.manager = DatabaseManager(db_path)
        self.expiry_hours = int(os.getenv('EMAIL_VERIFICATION_EXPIRY_HOURS', '48'))
        self.base_url = get_email_verification_base_url()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @staticmethod
    def _generate_code() -> str:
        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    @staticmethod
    def _format_database_timestamp(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    def prepare_verification(
        self,
        email: str,
        *,
        recipient_name: str = '',
        source: str = 'verification_request',
        template_name: str = DEFAULT_VERIFICATION_TEMPLATE,
        expiry_hours: Optional[int] = None,
        persist: bool = True,
    ) -> VerificationEmailPayload:
        """Create a verification payload and optionally persist it."""
        normalized_email = email.strip().lower()
        expires_delta = timedelta(hours=expiry_hours or self.expiry_hours)
        expires_at = datetime.now(timezone.utc) + expires_delta
        token = secrets.token_urlsafe(32)
        code = self._generate_code()
        verification_link = build_verification_link(self.base_url, token)

        payload = VerificationEmailPayload(
            email=normalized_email,
            token=token,
            verification_code=code,
            expires_at=self._format_timestamp(expires_at),
            verification_link=verification_link,
            template_name=template_name,
        )

        if not persist:
            return payload

        contact_id = self.manager.upsert_contact_for_verification(
            normalized_email,
            name=recipient_name,
            source=source,
        )
        request_id = self.manager.create_verification_request(
            contact_id=contact_id,
            email=normalized_email,
            token_hash=self._hash_token(token),
            verification_code=code,
            expires_at=self._format_database_timestamp(expires_at),
            template_name=template_name,
        )
        payload.contact_id = contact_id
        payload.request_id = request_id
        return payload

    def confirm(
        self,
        *,
        token: Optional[str] = None,
        email: Optional[str] = None,
        verification_code: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, object]]]:
        """Confirm an email with either a token or an email + code pair."""
        token_hash = self._hash_token(token) if token else None
        return self.manager.confirm_verification(
            token_hash=token_hash,
            email=email,
            verification_code=verification_code,
        )

    def mark_sent(self, request_id: Optional[int]) -> bool:
        """Mark a verification request as successfully delivered."""
        if not request_id:
            return False
        return self.manager.set_verification_request_status(request_id, 'sent')

    def mark_failed(self, request_id: Optional[int]) -> bool:
        """Mark a verification request as failed to deliver."""
        if not request_id:
            return False
        return self.manager.set_verification_request_status(request_id, 'failed')

    def get_status(self, email: str) -> Optional[Dict[str, object]]:
        """Fetch the current verification status for an email."""
        return self.manager.get_verification_status(email)
