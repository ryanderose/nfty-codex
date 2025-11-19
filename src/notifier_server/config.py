"""Configuration helpers for the Codex → ntfy FastMCP server."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Final
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOGGER = logging.getLogger(__name__)

PRIORITY_MAP: Final[dict[str, int]] = {
    "min": 1,
    "low": 2,
    "default": 3,
    "high": 4,
    "urgent": 5,
}

_DEFAULT_PRIORITY: Final[str] = "default"
_ENV_LOADED = False
_ENV_FILE_OVERRIDE_ENV = "NOTIFIER_ENV_FILE"


class ConfigSettings(BaseSettings):
    """Validated configuration sourced from environment variables/.env."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="forbid",
    )

    ntfy_base_url: str = Field(
        default="https://ntfy.sh",
        description="Base URL for the ntfy server (must be HTTPS).",
    )
    ntfy_topic: str = Field(
        description="High-entropy ntfy topic that the mobile/web clients subscribe to.",
    )
    ntfy_token: str | None = Field(
        default=None,
        description="Optional bearer token for authenticated topics.",
    )
    default_priority: str = Field(
        default=_DEFAULT_PRIORITY,
        description="Fallback priority applied when Codex omits the field.",
        validation_alias=AliasChoices("NOTIFY_DEFAULT_PRIORITY", "DEFAULT_PRIORITY"),
    )
    default_category: str | None = Field(
        default=None,
        description="Optional default category/tag (maps to ntfy tags).",
        validation_alias=AliasChoices("NOTIFY_DEFAULT_CATEGORY", "DEFAULT_CATEGORY"),
    )

    @field_validator("ntfy_base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        parsed = urlparse(cleaned)
        if parsed.scheme != "https":
            msg = "NTFY_BASE_URL must start with https://"
            raise ValueError(msg)
        if not parsed.netloc:
            msg = "NTFY_BASE_URL must include a hostname"
            raise ValueError(msg)
        return cleaned

    @field_validator("ntfy_topic")
    @classmethod
    def _validate_topic(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "NTFY_TOPIC cannot be empty"
            raise ValueError(msg)
        return cleaned

    @field_validator("default_priority")
    @classmethod
    def _normalize_priority(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PRIORITY_MAP:
            LOGGER.warning(
                "Invalid priority '%s' detected; falling back to '%s'",
                value,
                _DEFAULT_PRIORITY,
            )
            return _DEFAULT_PRIORITY
        return normalized

    @field_validator("default_category")
    @classmethod
    def _normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


def _ensure_env_loaded() -> None:
    global _ENV_LOADED
    if not _ENV_LOADED:
        env_file_override = os.getenv(_ENV_FILE_OVERRIDE_ENV) or None
        load_dotenv(env_file_override, override=False)
        _ENV_LOADED = True


@lru_cache(maxsize=1)
def _load_settings_cached() -> ConfigSettings:
    _ensure_env_loaded()
    return ConfigSettings()


def load_settings() -> ConfigSettings:
    """Return cached settings instance."""

    return _load_settings_cached()


def reset_settings_cache() -> None:
    """Clear cached settings; intended for tests."""

    global _ENV_LOADED
    _ENV_LOADED = False
    _load_settings_cached.cache_clear()


__all__ = [
    "ConfigSettings",
    "PRIORITY_MAP",
    "load_settings",
    "reset_settings_cache",
    "ValidationError",
]
