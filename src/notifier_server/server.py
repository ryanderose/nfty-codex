"""FastMCP server exposing the notify_mobile tool for Codex.

The full behavior is described in `docs/initial-spec/2025-11-18-codex-ntfy-spec.md`.
This module wires a stub transport so contributors can validate Codex integration
before real ntfy HTTP requests are implemented.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from notifier_server.config import (
    PRIORITY_MAP,
    ValidationError,
    load_settings,
    reset_settings_cache,
)

LOGGER = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 512
DEFAULT_TITLE = "Codex task status"

server = FastMCP("codex-notifier")


def _redact_token(token: str | None) -> str | None:
    if not token:
        return None
    if len(token) <= 8:
        return "***REDACTED***"
    return f"{token[:4]}…{token[-2:]}"


def _compose_body(message: str, include_repo: bool) -> str:
    trimmed = message.strip()
    if not include_repo:
        return trimmed
    repo_name = Path.cwd().name
    return f"{trimmed} (repo: {repo_name})"


def _normalize_priority(priority: str | None, default_priority: str) -> tuple[str, str | None]:
    if not priority:
        return default_priority, None
    normalized = priority.strip().lower()
    if normalized in PRIORITY_MAP:
        return normalized, None
    note = f"Priority '{priority}' is not supported; falling back to '{default_priority}'."
    return default_priority, note


def _build_headers(
    token: str | None,
    title: str,
    priority: str,
    category: str | None,
) -> dict[str, Any]:
    tags = ["codex"]
    if category and category not in tags:
        tags.append(category)

    headers: dict[str, Any] = {
        "Title": title,
        "Priority": PRIORITY_MAP[priority],
    }
    if tags:
        headers["Tags"] = ",".join(tags)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _log_payload(payload: dict[str, Any]) -> None:
    printable = dict(payload)
    headers = dict(printable.get("headers", {}))
    auth_value = headers.get("Authorization")
    if auth_value:
        headers["Authorization"] = (
            f"Bearer {_redact_token(auth_value.removeprefix('Bearer ').strip())}"
        )
    printable["headers"] = headers
    LOGGER.info("Prepared payload: %s", json.dumps(printable))


async def _stub_http_send() -> None:
    async with httpx.AsyncClient() as client:
        await client.aclose()


@server.tool()
async def notify_mobile(
    message: str,
    title: str = DEFAULT_TITLE,
    priority: str = "default",
    category: str | None = None,
    include_repo: bool = False,
) -> str:
    """Send a single mobile notification via ntfy.

    Use this after long-running/critical Codex tasks complete, on blocking failures, or
    when the user explicitly asked for a phone notification. Keep messages short,
    avoid source code/secrets, and only include repo context when needed.
    """

    if not message.strip():
        return "Notification not sent: message is required."
    if len(message) > MAX_MESSAGE_LENGTH:
        return (
            f"Notification not sent: message is too long (limit {MAX_MESSAGE_LENGTH} characters)."
        )

    try:
        settings = load_settings()
    except ValidationError as exc:  # pragma: no cover - exercised indirectly
        LOGGER.warning("Configuration error: %s", exc)
        return (
            "Notification not sent: configuration error. Ensure NTFY_TOPIC and related"
            " environment variables are set."
        )

    normalized_priority, note = _normalize_priority(priority, settings.default_priority)
    resolved_category = category or settings.default_category
    body = _compose_body(message, include_repo)
    headers = _build_headers(settings.ntfy_token, title, normalized_priority, resolved_category)
    payload = {
        "url": f"{settings.ntfy_base_url}/{settings.ntfy_topic}",
        "headers": headers,
        "body": body,
    }
    _log_payload(payload)
    await _stub_http_send()

    response_parts = [
        "Notification prepared for topic "
        f"'{settings.ntfy_topic}' with priority '{normalized_priority}'.",
        "HTTP delivery is stubbed for this milestone; no ntfy request was sent.",
    ]
    if note:
        response_parts.insert(1, note)
    return " ".join(response_parts)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Codex ntfy FastMCP server.")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="Transport protocol to use when running the server.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Load configuration and exit without starting the server.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.check:
        try:
            settings = load_settings()
            LOGGER.info(
                "Configuration OK for topic '%s' using base %s",
                settings.ntfy_topic,
                settings.ntfy_base_url,
            )
        except ValidationError as exc:  # pragma: no cover - exercised via CLI tests
            LOGGER.error("Configuration invalid: %s", exc)
            return 1
        return 0

    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        LOGGER.info("Server stopped by user")
        return 0
    finally:
        reset_settings_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
