# Spec: Initial Build & Scaffolding for Codex → ntfy Notification Workflow

Version 0.1 — 2025-11-20

This document translates the high-level notification workflow defined in `docs/initial-spec/2025-11-18-codex-ntfy-spec.md` into a concrete first implementation plan for the (currently empty) repository. It focuses on delivering the minimum viable structure so contributors can start iterating on the MCP server, documentation, and integration points immediately.

---

## 1. Objectives

1. Produce a working repository skeleton that captures the architectural intent from the initial spec.
2. Ship a runnable (but minimal) Python MCP server that already exposes the `notify_mobile` tool with stubbed logic for ntfy calls.
3. Provide docs, scripts, and configuration samples so future contributors can quickly finish the full implementation.
4. Keep scope tight: we only stand up the scaffolding that unblocks iterative development and validation.

---

## 2. Deliverables Overview

| Area | Deliverable |
| --- | --- |
| Repository hygiene | `.gitignore`, `README.md`, `docs/` tree with cross-links |
| Python project | `pyproject.toml`, `uv.lock` (optional after first `uv pip compile`), `src/notifier_server/` package |
| MCP server entrypoint | `src/notifier_server/server.py` implemented with FastMCP skeleton |
| Configuration samples | `.env.example`, `docs/setup/env-vars.md` |
| Developer tooling | `Makefile` (or `justfile`) with `dev`, `lint`, and `notify:test` commands |
| Validation assets | `docs/setup/manual-test-checklist.md`, sample Codex `config.toml` snippet |

---

## 3. Target Directory Layout

```
docs/
  initial-spec/
  setup/
    env-vars.md
    manual-test-checklist.md
  specs/
    2025-11-20-initial-build-scaffolding.md
src/
  notifier_server/
    __init__.py
    server.py
    config.py
scripts/
  send_test_notification.py
.env.example
.gitignore
Makefile (or justfile)
pyproject.toml
README.md
```

Notes:
- `config.py` centralizes env handling (`NTFY_BASE_URL`, `NTFY_TOPIC`, `NTFY_TOKEN`, default priority) with validation helpers that mirror §5.1.4 of the main spec.
- `scripts/send_test_notification.py` lets developers send a manual notification outside Codex to verify ntfy configuration quickly.

---

## 4. Python Project Scaffolding

### 4.1 Tooling
- Use **Python 3.11+**.
- Manage dependencies with **uv**; document install instructions in `README.md`.
- Declare dependencies in `pyproject.toml`:
  - Required: `mcp`, `httpx`, `pydantic` (for config validation), `python-dotenv` (optional for local `.env`).
  - Dev extras: `ruff`, `pytest`, `pytest-asyncio`.

### 4.2 FastMCP Server Skeleton (`src/notifier_server/server.py`)
- Instantiate `FastMCP` server with name `codex-notifier`.
- Register `notify_mobile` tool with signature described in §5.1.2 of the initial spec.
- Implement logic phases:
  1. **Input validation** (length limit, forbidden substrings).
  2. **Config load** using `ConfigSettings` from `config.py`.
  3. **HTTP call placeholder**: for the initial build, log the intended payload and return a stubbed success string; wire `httpx.AsyncClient` but guard real POST behind `if settings.ntfy_topic`.
  4. **Error handling**: wrap in try/except and always return user-facing text (per §5.1.3).
- Include `if __name__ == "__main__"` entrypoint calling `server.run()` so the script can be launched standalone or via `uv run`.

### 4.3 Config Module (`src/notifier_server/config.py`)
- Define `ConfigSettings` dataclass/pydantic model with fields for each env variable.
- Provide helper `load_settings()` that merges `.env` (optional), environment variables, and defaults.
- Validate:
  - `ntfy_topic` is non-empty.
  - `priority` is in allowed set.
  - `base_url` is HTTPS.
- Expose `PRIORITY_MAP` that converts human-friendly values to ntfy integers for later implementation.

---

## 5. Developer Experience Assets

### 5.1 README.md
Must cover:
1. Project description + link back to the original spec.
2. Quick start (install uv, create virtual env, run server in dev mode).
3. How to configure `NTFY_*` variables (link to `docs/setup/env-vars.md`).
4. Example Codex `config.toml` snippet so users can register the MCP server immediately.
5. Testing instructions referencing `scripts/send_test_notification.py` and the manual checklist.

### 5.2 Makefile / Justfile Targets
- `setup`: install uv, sync dependencies (`uv pip install -r pyproject.toml` or `uv sync`).
- `dev`: run the MCP server with hot reload using `uv run --watch src/notifier_server/server.py` (if using `watchfiles`).
- `lint`: run `ruff check src scripts`. 
- `format`: run `ruff format` (even if minimal now).
- `notify:test`: execute `scripts/send_test_notification.py --message "Test" --priority high` to verify ntfy pipeline.

### 5.3 Sample Config Snippets
- `docs/setup/env-vars.md` lists env variables, defaults, and rationale (mirrors §5.1.4).
- Provide `.env.example` with placeholders and inline comments reminding users not to commit secrets.

---

## 6. Integration with Codex CLI

1. Document precise `config.toml` block, e.g.:
   ```toml
   [mcp_servers.codex-notifier]
   command = "uv"
   args = [
     "run",
     "--with", "mcp[cli]",
     "--with", "httpx",
     "--with", "pydantic",
     "/absolute/path/to/src/notifier_server/server.py"
   ]
   ```
2. Add `docs/setup/manual-test-checklist.md` item that tells developers to start Codex, ask it to call `notify_mobile`, and confirm the stub returns expected text.
3. Until the HTTP layer is finished, instruct users that the tool returns a stub message; they can still validate wiring end-to-end.

---

## 7. Validation for Initial Build

To consider the scaffolding complete, ensure:
- `uv run src/notifier_server/server.py --help` (or equivalent) starts without errors.
- `scripts/send_test_notification.py` reads `.env` and prints the payload it would send to ntfy.
- `codex` (CLI or VS Code) lists `notify_mobile` in tool inventory after the config snippet is added.
- Linting (`ruff check`) passes on CI or local run.

---

## 8. Out of Scope for This Milestone

- Actual HTTP POST to ntfy (can be toggled on later once credentials exist).
- Semantic heuristics for when Codex should call the tool (handled at prompting level per initial spec).
- Mobile client onboarding tutorials beyond linking to ntfy docs.

---

## 9. Next Steps After Scaffolding

1. Implement real ntfy HTTP call with retry/backoff logic.
2. Add telemetry/logging polish and redact-sensitive info.
3. Expand docs with troubleshooting (network auth, proxies, etc.).
4. Automate testing (unit tests for config + notification payload builder).

