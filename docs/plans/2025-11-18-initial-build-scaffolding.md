# Initial Build Scaffolding — Implementation Plan

## Overview
- Stand up the Codex → ntfy notification repository with the exact scaffolding defined in the 2025-11-20 spec so engineers can immediately iterate on the MCP server and integration assets.
- Provide a runnable FastMCP stub exposing `notify_mobile`, centralized configuration helpers, and starter docs/scripts for setup and validation.
- Ticket: Initial ntfy notification scaffolding (per `docs/specs/2025-11-20-initial-build-scaffolding.md`).

## Current State (from Research)
- Repository currently contains only specs (`docs/specs/2025-11-20-initial-build-scaffolding.md`, `docs/initial-spec/2025-11-18-codex-ntfy-spec.md`) with no `src/`, tooling, or docs beyond the specs (`docs/research/2025-11-18-initial-build-scaffolding-research.md:36-87`).
- Deliverables, directory layout, and validation expectations are fully enumerated in the scaffolding spec (`docs/specs/2025-11-20-initial-build-scaffolding.md:18-140`).
- Key risks already noted: missing ntfy topic/secret validation, Codex config mis-wiring, and MCP trust boundary (no Seatbelt/Landlock) (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:300-425`).
- Key files/modules to introduce:
  - `src/notifier_server/server.py` — FastMCP entrypoint exposing `notify_mobile` per main spec §5.1 (`docs/specs/2025-11-20-initial-build-scaffolding.md:70-78`).
  - `src/notifier_server/config.py` — Env handling and validation for `NTFY_*` vars with priority map (`docs/specs/2025-11-20-initial-build-scaffolding.md:55-88`).
  - `scripts/send_test_notification.py` — Manual test helper for ntfy payloads (`docs/specs/2025-11-20-initial-build-scaffolding.md:33-42`).

## Desired End State
- Developers can clone the repo, run `uv sync`, start `src/notifier_server/server.py`, and see `notify_mobile` in Codex using the documented config snippet.
- `.env.example`, `docs/setup/env-vars.md`, and `docs/setup/manual-test-checklist.md` describe configuration and manual verification.
- `Makefile` targets (`setup`, `dev`, `lint`, `format`, `notify:test`) wrap the uv/ruff workflows.
- Automated checks (lint, pytest, stubbed integration) run cleanly; manual checklist verifies Codex lists the tool and stubbed responses surface.

## Non-Goals
- Sending real ntfy requests by default (HTTP POST remains stubbed until credentials exist, per spec §8).
- Advanced notification heuristics or Codex prompt wiring beyond providing the documented tool contract.
- Telemetry/observability beyond local logging; no deployment automation or packaging beyond uv/pyproject scaffolding.

## Architecture & Approach
- Layered structure: config validation (`src/notifier_server/config.py`) feeds the FastMCP server (`server.py`); scripts/docs guide manual usage. Dependencies managed via uv (`pyproject.toml`) with Ruff/Pytest as dev tools, matching spec instructions (`docs/specs/2025-11-20-initial-build-scaffolding.md:43-68`).
- FastMCP server registers `notify_mobile`, performs validation, loads config, logs payload (stub), and returns user-facing text per main spec §5.1.3 (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:139-210`).
- `.env` loading via python-dotenv ensures local setups match env docs, while `.env.example` + `docs/setup/env-vars.md` keep secrets out of git.
- **Alternatives considered**:
  - `justfile` vs `Makefile`: choose `Makefile` to avoid requiring `just` and align with spec default (Makefile listed first) while still enabling portability.
  - Dataclass + manual parsing vs `pydantic.BaseSettings`: spec explicitly calls for pydantic validation; sticking with `pydantic-settings` gives declarative validation/error messaging for env vars.

## Phases

### Phase 1 — Repository Skeleton & Docs
**Goal:** Establish folder structure, project metadata, and onboarding docs/tooling so contributors can install deps and understand expectations.

**Changes**
- Code: `.gitignore` — Ignore uv artifacts, `__pycache__`, `.ruff_cache`, `.env`, `.python-version`.
- Code: `pyproject.toml` + optional `uv.lock` — Define Python 3.11, dependencies (`mcp`, `httpx`, `pydantic`, `python-dotenv`) and dev dependencies (`ruff`, `pytest`, `pytest-asyncio`).
- Code: `Makefile` — Targets `setup`, `dev`, `lint`, `format`, `notify:test`, ensuring commands wrap uv and scripts.
- Code: `src/notifier_server/__init__.py` — Empty module file plus package docstring referencing spec.
- Docs: `README.md` — Overview, setup steps, uv instructions, link to main spec & env docs, Codex config snippet placeholder.
- Docs: `docs/setup/env-vars.md` — Table for each `NTFY_*` var with default, source, validation, mapping to `ConfigSettings`.
- Docs: `docs/setup/manual-test-checklist.md` — Sequence: configure `.env`, run `make dev`, run `scripts/send_test_notification.py`, add Codex config, request `notify_mobile`.
- Docs: Directory scaffolding for `docs/setup/` and ensuring spec cross-links.

**Notes**
- Provide consistent relative paths (e.g., `src/notifier_server/server.py`) for cross-references.
- Document `uv` installation prerequisites (curl script or `pip install uv`) and highlight Python 3.11+ requirement.

**Success Criteria**  
**Automated**
- [x] Dependency graph resolves: `uv sync` (or `make setup`) completes without errors.
- [x] Ruff available: `uv run ruff --version` executes (verifies dev dependency wiring).
- [x] Placeholder lint: `make lint` (runs `uv run ruff check src scripts`) succeeds on empty tree.
- [x] Placeholder tests: `uv run pytest -q` passes (even with zero tests) proving tooling works.
**Manual**
- [ ] README quick-start instructions reproduce install+dev steps on a clean machine.
- [ ] Docs cross-link to specs and clearly outline environment expectations.
- [ ] `Makefile` targets documented/tests by maintainers for correct command output.

---

### Phase 2 — Config Module & Test Utilities
**Goal:** Implement configuration loading/validation and supporting utilities so ntfy payloads and env docs stay in sync.

**Changes**
- Code: `src/notifier_server/config.py` — `ConfigSettings` (pydantic BaseSettings) with fields `ntfy_base_url`, `ntfy_topic`, `ntfy_token`, `default_priority`, `category`. Include validation (HTTPS base URL, non-empty topic) and `PRIORITY_MAP` translating friendly priority strings to ntfy integers. Provide `load_settings()` helper caching `.env` values via python-dotenv.
- Code: `scripts/send_test_notification.py` — CLI using argparse (message, title, priority, category, include-repo) that loads `ConfigSettings`, builds payload, and logs/prints intended POST (no real HTTP yet). Supports `--dry-run` (default) and `--execute` toggle for future real POST.
- Code: `tests/test_config.py` (optional but recommended) — Validate env parsing, default priority, priority normalization, and error messages for missing topic.
- Docs: Update `.env.example` with annotated variables (NTFY_BASE_URL, NTFY_TOPIC, NTFY_TOKEN, NOTIFY_DEFAULT_PRIORITY) and reference `docs/setup/env-vars.md`.
- Docs: Extend `docs/setup/env-vars.md` with validation rules gleaned from config implementation.

**Notes**
- Use `pydantic-settings` `SettingsConfigDict(env_file='.env', extra='forbid')` to block typos.
- Document usage in README and manual checklist so users run `cp .env.example .env` and fill values.

**Success Criteria**  
**Automated**
- [x] Type/build sanity: `uv run python -m compileall src/notifier_server/config.py`.
- [x] Unit tests: `uv run pytest tests/test_config.py -q` cover validation edges and priority map.
- [x] Lint/style: `make lint` + `make format` (Ruff format) complete cleanly.
**Manual**
- [x] `.env.example` loads via `load_settings()` without exceptions when filled with sample values.
- [x] Running `uv run scripts/send_test_notification.py --message 'Ping' --priority high` logs payload details referencing env vars.
- [x] Manual checklist updated with script usage and expected output.

---

### Phase 3 — FastMCP Server Stub & Codex Integration Assets
**Goal:** Deliver the runnable MCP server exposing `notify_mobile`, integrate docs/snippets, and validate end-to-end stubbed workflow.

**Changes**
- Code: `src/notifier_server/server.py` — Instantiate `FastMCP(name="codex-notifier")`, define async `notify_mobile` tool (message/title/priority/category/include_repo) with docstring guidance, call `load_settings()`, run validation logic, log payload, and return stub success string. Include error handling returning friendly messages and `if __name__ == "__main__": server.run()` entrypoint.
- Code: Optional `tests/test_server.py` with async tests exercising tool invocation via FastMCP client or direct coroutine, ensuring validation errors bubble as spec’d.
- Docs: Update `README.md` with full Codex `config.toml` snippet, manual invocation instructions (`uv run src/notifier_server/server.py`), and linking to manual checklist.
- Docs: `docs/setup/manual-test-checklist.md` — Add steps to start server, run `codex --list-tools`, call `notify_mobile`, and confirm stub output.
- Config/Infra: Ensure `Makefile` `dev` runs `uv run --watch src/notifier_server/server.py` (if `watchfiles` added) or at least `uv run src/notifier_server/server.py`. `notify:test` target executes sample script with default message.

**Notes**
- Keep HTTP call stubbed but wire `httpx.AsyncClient` context + placeholder comment for future POST; log payload with sensitive fields redacted.
- Document fallback behavior when env vars missing (tool returns helpful error message instead of crash).

**Success Criteria**  
**Automated**
- [x] Server runs: `uv run src/notifier_server/server.py --help` (or `uv run src/notifier_server/server.py` + manual exit) executes without stack traces.
- [x] Tool test: `uv run pytest tests/test_server.py -q` (or equivalent) ensures `notify_mobile` handles good/bad input.
- [x] Lint/style: `make lint` & `make format` remain clean after server logic is added.
- [x] Integration smoke: `make notify:test` executes `scripts/send_test_notification.py` successfully using stubbed HTTP.
**Manual**
- [ ] Codex config snippet copied into `~/.codex/config.toml` yields `notify_mobile` in `codex tools` listing.
- [ ] Manual checklist passes: running `notify_mobile` via Codex returns stub response referencing message + topic.
- [ ] Logging shows payload JSON with sensitive fields redacted and no exceptions during typical use.

## Testing Strategy
- **Unit tests**: Cover `ConfigSettings` parsing (missing topic, invalid URL, priority normalization) and `notify_mobile` behavior (invalid message length, include_repo flag). Use `pytest-asyncio` for async tool tests and mock `httpx.AsyncClient` to avoid network traffic.
- **Integration/E2E**: Manual checklist plus script-driven smoke tests ensure `scripts/send_test_notification.py` and FastMCP server behave with `.env` values; optional integration test using `subprocess` to spawn server and interact via FastMCP client stub.
- **Observability**: Add structured logging within `server.py` (INFO for payload summary, WARNING for validation issues, ERROR for exceptions) and ensure logs never leak tokens (mask values in log output).

## Performance & Security
- Performance: Keep stub lightweight; verify server startup <1s locally. Document expectation that `notify_mobile` remains non-blocking by using async HTTP client even while stubbed.
- Security: Enforce HTTPS base URL, require non-empty ntfy topic/token, forbid logging secrets, and remind users `.env` is gitignored. Document trust boundary (MCP server runs outside host sandbox) and encourage random ntfy topics (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:300-420`).

## Migration & Rollback
- Migration: No persisted data; introducing scaffolding is additive. Should rollback be required, remove new directories/files introduced in phases and revert `pyproject.toml`. Keep `.env` gitignored to prevent leaking secrets.
- Backfill: None required, but ensure `.env.example` + docs stay synchronized if fields change. Provide instructions for regenerating `uv.lock` if dependency versions need pinning.
- Rollback safety: Because server is stubbed, disabling `mcp_servers.codex-notifier` entry in Codex config immediately stops usage.

## Risks & Mitigations
- Missing/invalid env vars → Mitigate with pydantic validation + clear error messages surfaced to tool output and docs.
- Developers skip manual checklist → Mitigate by linking checklist prominently in README and referencing `make notify:test` in PR template (future work).
- Tool signature drift vs main spec → Mitigate by copying signature/description verbatim from `docs/initial-spec/2025-11-18-codex-ntfy-spec.md` and adding unit tests for schema.
- uv unfamiliarity → Mitigate by documenting install + fallback `pip` commands, plus referencing uv docs in README.

## References
- Spec: `docs/specs/2025-11-20-initial-build-scaffolding.md`
- Research: `docs/research/2025-11-18-initial-build-scaffolding-research.md`
- Core behavior reference: `docs/initial-spec/2025-11-18-codex-ntfy-spec.md`
