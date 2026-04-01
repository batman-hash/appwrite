"""Shared email-campaign utilities used by the kernel bridge scripts."""

from .database_manager import DatabaseManager
from .email_extractor import EmailExtractor, EmailValidator, get_email_extractor
from .email_verification import (
    DEFAULT_VERIFICATION_TEMPLATE,
    EmailVerificationService,
    VerificationEmailPayload,
)
from .template_manager import TemplateManager
from .auto_email_extractor import AutoEmailExtractor

