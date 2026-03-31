"""
Secure local storage helpers for API keys.

Keys are read from environment variables first, then from a local secrets
directory with restrictive filesystem permissions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent
SECRETS_DIR = BASE_DIR / "secrets"


def _sanitize_name(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "api_key"


def ensure_secrets_dir() -> Path:
    """Create the secrets directory with owner-only permissions."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(SECRETS_DIR, 0o700)
    except OSError:
        pass
    return SECRETS_DIR


def secret_path(name: str) -> Path:
    """Return the on-disk path for a secret name."""
    ensure_secrets_dir()
    return SECRETS_DIR / f"{_sanitize_name(name)}.key"


def read_secret(name: str) -> Optional[str]:
    """Read a secret from disk if it exists."""
    path = secret_path(name)
    try:
        if not path.is_file():
            return None
        value = path.read_text(encoding="utf-8").strip()
        return value or None
    except OSError:
        return None


def write_secret(name: str, value: str, overwrite: bool = False) -> Path:
    """Store a secret securely on disk."""
    if not value or not value.strip():
        raise ValueError("Secret value cannot be empty")

    path = secret_path(name)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Secret already exists at {path}")

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value.strip() + "\n")
    finally:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    return path


def delete_secret(name: str) -> bool:
    """Delete a stored secret if present."""
    path = secret_path(name)
    try:
        if path.exists():
            path.unlink()
            return True
    except OSError:
        return False
    return False


def load_api_key(env_name: str, secret_name: Optional[str] = None) -> Optional[str]:
    """Load an API key from the environment or the secrets directory."""
    env_value = os.getenv(env_name, "").strip()
    if env_value:
        return env_value

    candidate_names = [secret_name, env_name.lower()]
    for candidate in candidate_names:
        if candidate:
            value = read_secret(candidate)
            if value:
                return value
    return None
