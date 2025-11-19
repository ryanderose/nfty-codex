# Environment Variables

The FastMCP server reads a small set of environment variables to determine how to talk to ntfy. These values will be parsed by `ConfigSettings` in `src/notifier_server/config.py` during Phase 2 of the plan, but we document the contract up front so contributors know what to provision.

| Variable | Required | Default | Description | Validation/Notes |
| --- | --- | --- | --- | --- |
| `NTFY_BASE_URL` | No | `https://ntfy.sh` | Base URL for the ntfy instance handling notifications. | Must be HTTPS when overridden. Trailing slash is trimmed automatically. |
| `NTFY_TOPIC` | **Yes** | _None_ | Unique topic name that the ntfy app subscribes to (e.g., `codex-notify-<uuid>`). | Cannot be empty. Leading/trailing whitespace is stripped. Use a high-entropy topic per [`docs/initial-spec/2025-11-18-codex-ntfy-spec.md`](../initial-spec/2025-11-18-codex-ntfy-spec.md). |
| `NTFY_TOKEN` | No | _None_ | Bearer token used when your ntfy topic requires authentication. | When set, requests include `Authorization: Bearer <token>`. Leave unset for anonymous topics. |
| `NOTIFY_DEFAULT_PRIORITY` | No | `default` | Priority (`min`, `low`, `default`, `high`, `urgent`) applied when Codex omits an explicit priority. | Value is validated against the priority map. Invalid strings fall back to `default` and log a warning. |
| `NOTIFY_DEFAULT_CATEGORY` | No | _None_ | Optional tag/category appended to each notification when Codex does not supply one. | Categories map to ntfy tags (emoji or plain text). Leave blank to skip. |

## Loading Order

1. Values in a local `.env` file (see `.env.example`, added in Phase 2) are read first.
2. Environment variables exported in your shell override `.env` entries.
3. Defaults shown above are used when a value is still missing (except for `NTFY_TOPIC`, which is required).

> Tip: start from `.env.example` in the repo root, rename it to `.env`, and edit the placeholders. The `python-dotenv` integration automatically reads the file when you launch the MCP server or run helper scripts.

> Advanced: set `NOTIFIER_ENV_FILE` to point at a specific env file if you need to keep secrets outside the repo or run tests in isolation. This is optional and mainly used by automated tests.

If validation fails, the MCP server will return a friendly error message to Codex instead of crashing. For full behavioral details see the main spec sections 5.1–5.2.
