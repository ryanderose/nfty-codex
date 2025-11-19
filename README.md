# Codex → ntfy Notification Scaffold

This repository contains the starter FastMCP project that lets Codex CLI expose a `notify_mobile` tool which ultimately sends notifications to the ntfy mobile/web apps. The goal of this milestone is to stand up the structure, tooling, and documentation that future contributors need to finish the full workflow described in [`docs/initial-spec/2025-11-18-codex-ntfy-spec.md`](docs/initial-spec/2025-11-18-codex-ntfy-spec.md) and the scaffolding supplement [`docs/specs/2025-11-20-initial-build-scaffolding.md`](docs/specs/2025-11-20-initial-build-scaffolding.md).

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for dependency management. Install via:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # or
  pip install uv
  ```
- Access to Codex CLI / VS Code extension (for later manual verification)

## Quick Start

```bash
# Install dependencies
uv sync

# Copy the sample env file and fill in your topic/token later
cp .env.example .env

# Check formatting/linting works
make lint

# Run the test suite (config + scaffolding checks)
uv run pytest -q

# Confirm the MCP server can load configuration and exit
uv run python -m src/notifier_server.server --check

# Start the FastMCP server (Ctrl+C to stop)
make dev
```

The `src/notifier_server/` package is where the FastMCP server and configuration helpers live, while `scripts/` contains manual testing utilities such as `send_test_notification.py`.

## Configuration & Environment

Environment variables used by the MCP server are documented in [`docs/setup/env-vars.md`](docs/setup/env-vars.md). Start from `.env.example`, copy it to `.env`, and fill in your ntfy topic/token. Run `uv run python -m src/notifier_server.server --check` anytime you want to confirm the settings are valid before launching the server.

## Codex Integration

Codex CLI discovers MCP servers through `~/.codex/config.toml`. This scaffold documents the snippet you will add once the FastMCP server lands:

```toml
[mcp_servers.codex-notifier]
command = "uv"
args = [
  "run",
  "--with", "mcp[cli]",
  "--with", "httpx",
  "--with", "pydantic",
  "--with", "pydantic-settings",
  "--with", "python-dotenv",
  "/absolute/path/to/src/notifier_server/server.py"
]
```

Replace the script path with the absolute path inside your repo (Codex launches MCP servers from arbitrary directories, so absolute paths are required). After editing the config file restart Codex CLI (or the VS Code extension) and run `codex --list-tools` to confirm `notify_mobile` appears.

## Validation & Manual Testing

Manual verification steps live in [`docs/setup/manual-test-checklist.md`](docs/setup/manual-test-checklist.md). They walk through preparing `.env`, running the dev server (`make dev`), invoking the notification script, wiring Codex via `config.toml`, and confirming Codex can call the stubbed `notify_mobile` tool end-to-end.

### Notification script

Use `make notify:test` (or call `scripts/send_test_notification.py` directly) to inspect the payload that will eventually be POSTed to ntfy:

```bash
uv run python scripts/send_test_notification.py --message "Codex manual test" --dry-run
```

The script loads `ConfigSettings`, resolves priorities/categories, and prints a JSON payload with the bearer token redacted. HTTP execution remains stubbed until real ntfy wiring lands.

## Makefile Targets

| Target       | Description |
| ------------ | ----------- |
| `make setup` | Run `uv sync` to ensure dependencies are installed. |
| `make dev`   | Launch the FastMCP server (`uv run python -m src.notifier_server.server`). |
| `make lint`  | Run `ruff check` across `src/` and `scripts/`. |
| `make format`| Run `ruff format` to auto-format source files. |
| `make notify:test` | Execute `scripts/send_test_notification.py` (requires `NTFY_TOPIC`). |

Each target intentionally wraps `uv run ...` so contributors do not have to manage local virtual environments manually.

## Additional Documentation

- [`docs/specs/2025-11-20-initial-build-scaffolding.md`](docs/specs/2025-11-20-initial-build-scaffolding.md)
- [`docs/initial-spec/2025-11-18-codex-ntfy-spec.md`](docs/initial-spec/2025-11-18-codex-ntfy-spec.md)
- [`docs/research/2025-11-18-initial-build-scaffolding-research.md`](docs/research/2025-11-18-initial-build-scaffolding-research.md)
