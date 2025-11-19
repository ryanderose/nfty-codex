"""Helper script to preview ntfy payloads for manual testing."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from notifier_server.config import (
    PRIORITY_MAP,
    ConfigSettings,
    ValidationError,
    load_settings,
)

LOGGER = logging.getLogger("notifier_server.scripts.send_test_notification")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview the notification payload that will be sent to ntfy."
    )
    parser.add_argument(
        "--message",
        required=True,
        help="Notification body to send (concise summary only).",
    )
    parser.add_argument(
        "--title",
        default="Codex task status",
        help="Notification title (maps to the ntfy Title header).",
    )
    parser.add_argument(
        "--priority",
        choices=sorted(PRIORITY_MAP.keys()),
        help="Override the priority for this message.",
    )
    parser.add_argument(
        "--category",
        help="Optional category/tag that maps to ntfy tags.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the payload without attempting network I/O (default behavior).",
    )
    parser.add_argument(
        "--include-repo",
        action="store_true",
        help="Append the current repository name to the message body.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Reserved for future real HTTP POST support. Currently still a dry run.",
    )
    return parser.parse_args()


def _redact_token(token: str | None) -> str | None:
    if not token:
        return None
    if len(token) <= 8:
        return "***REDACTED***"
    return f"{token[:4]}…{token[-2:]}"


def _resolve_priority(settings: ConfigSettings, override: str | None) -> str:
    if override:
        return override
    return settings.default_priority


def _build_headers(
    settings: ConfigSettings, title: str, priority: str, category: str | None
) -> dict[str, Any]:
    tags: list[str] = ["codex"]
    resolved_category = category or settings.default_category
    if resolved_category and resolved_category not in tags:
        tags.append(resolved_category)

    headers: dict[str, Any] = {
        "Title": title,
        "Priority": PRIORITY_MAP[priority],
    }
    if tags:
        headers["Tags"] = ",".join(tags)
    if settings.ntfy_token:
        headers["Authorization"] = f"Bearer {settings.ntfy_token}"
    return headers


def _compose_message(message: str, include_repo: bool) -> str:
    if not include_repo:
        return message
    repo_name = Path.cwd().name
    return f"{message.strip()} (repo: {repo_name})"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args()

    try:
        settings = load_settings()
    except ValidationError as exc:  # pragma: no cover - exercised via tests
        LOGGER.error("Failed to load settings: %s", exc)
        return 1

    priority = _resolve_priority(settings, args.priority)
    category = args.category or settings.default_category
    headers = _build_headers(settings, args.title, priority, category)

    payload = {
        "url": f"{settings.ntfy_base_url}/{settings.ntfy_topic}",
        "headers": headers,
        "body": _compose_message(args.message, args.include_repo),
        "priority_label": priority,
    }

    printable_headers = dict(headers)
    if "Authorization" in printable_headers:
        printable_headers["Authorization"] = f"Bearer {_redact_token(settings.ntfy_token)}"

    LOGGER.info(
        "Prepared payload (dry-run%s)",
        ", execute flag ignored" if args.execute else "",
    )
    print(json.dumps({**payload, "headers": printable_headers}, indent=2))
    print("\nNOTE: HTTP execution is stubbed; pass --execute once the real POST is available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
