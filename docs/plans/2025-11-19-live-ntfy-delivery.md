# Live ntfy Delivery — Implementation Plan

## Overview
- Deliver Milestone 2 from `docs/specs/2025-11-25-live-ntfy-delivery.md` by turning the FastMCP `notify_mobile` tool and CLI helper into real ntfy clients while keeping dry‑run safeguards.
- Add shared HTTP logic, env‑driven controls, structured telemetry, and documentation/test coverage so contributors can diagnose issues quickly.
- Ticket/problem statement: enable live notification delivery and telemetry polish for Codex → ntfy workflow (research synopsis in `docs/research/2025-11-19-live-ntfy-delivery-research.md`).

## Current State (from Research)
- FastMCP server (`src/notifier_server/server.py:97`) validates inputs, logs a redacted payload, and calls `_stub_http_send`, so all flows are dry‑run only.
- CLI helper (`scripts/send_test_notification.py:21`) builds the payload, prints it, and ignores `--execute`, offering no network execution or retry knobs.
- Configuration model only exposes topic/token/defaults, lacking timeout/retry/enable flags or request ID support (`src/notifier_server/config.py:34`).
- Automated tests cover config validation and stubbed server responses only (`tests/test_server.py:29`); there is no coverage for HTTP client behavior, logging redaction on errors, or CLI code paths.
- Docs (`README.md:1`, `.env.example:3`, `docs/setup/env-vars.md:1`, `docs/setup/manual-test-checklist.md:1`) describe the stubbed flow and do not mention live send flags, troubleshooting, or telemetry guidance.
- Key files/modules:
  - `src/notifier_server/server.py:97` — FastMCP tool entry point.
  - `scripts/send_test_notification.py:21` — manual CLI helper.
  - `src/notifier_server/config.py:34` — env parsing.
  - `tests/test_server.py:29` — current async tool tests.

## Desired End State
- Both entry points reuse a hardened async HTTP client with configurable timeout, retry/backoff, request‑ID headers, and secure token handling, sending real ntfy POST/PUT calls when live mode is enabled.
- Structured logs emit key/value or JSON payloads with `event`, `topic`, `priority`, `request_id`, `status`, and sanitized response snippets; README documents summary counters/fields.
- Contributors can toggle live sends via `NOTIFY_ENABLE_LIVE_SEND` / CLI flags and override retry/timeouts; config docs and `.env.example` explain every knob.
- Tests cover success, retriable errors, permanent failures, timeout/backoff math, and token redaction, and docs/manual checklist describe how to verify live success/failure scenarios.
- Acceptance checks:
  - FastMCP `notify_mobile` sends and reports real ntfy responses (200 success, 4xx/5xx friendly errors).
  - `scripts/send_test_notification.py --execute` performs a real send with overrides and logs sanitized headers.
  - Manual checklist includes live send and induced failure steps with troubleshooting guidance.

## Non-Goals
- Support for transports other than ntfy (per spec scope).
- Scheduling, batching, or queueing notifications; each invocation remains one shot.
- Automated provisioning of ntfy topics/tokens or mobile confirmation flows.

## Architecture & Approach
- Introduce `src/notifier_server/http_client.py` that wraps `httpx.AsyncClient` with retry/backoff logic (statuses 500/502/503/504 + `httpx` errors + 429 respecting `Retry-After`), exponential jitter, timeout tuple, and request ID generation (prefix env + random suffix). Both the MCP tool and CLI call this helper so behavior stays consistent.
- Extend `ConfigSettings` with `NOTIFY_MAX_RETRIES`, `NOTIFY_TIMEOUT_SECONDS`, `NOTIFY_ENABLE_LIVE_SEND`, and `NOTIFY_REQUEST_ID_PREFIX`, plus derived properties for exponential backoff constants, and document them in `.env.example`/`docs/setup/env-vars.md`.
- Update `notify_mobile` to accept `live_send: bool = True` (default to env flag) and short‑circuit redacted dry‑run messaging when disabled. When enabled, pass sanitized payload + headers to the HTTP helper, map responses to user‑friendly messages, and log structured entries (JSON or key=value). Provide `X-Request-ID` header when request IDs are configured.
- Update `scripts/send_test_notification.py` to parse `--execute`, `--retries`, `--timeout`, and `--request-id-prefix`, call the shared helper synchronously via `asyncio.run`, and keep dry‑run as default. Print summary status + snippet for success/failure.
- Logging/telemetry: wrap log records via `LOGGER.info("event=notify_mobile ...")` or `json.dumps` with consistent fields, ensure tokens are redacted even when exceptions bubble up, and expose high‑level counters/instructions in README.
- Documentation: update README/manual checklist/troubleshooting to guide enabling live send, using CLI flags, verifying on ntfy web/mobile, and debugging 401/403/429/TLS issues.
- **Alternatives considered**
  - Separate HTTP logic in server & script: rejected because it duplicates retry/backoff and risks divergent behavior.
  - Making live send opt‑in via CLI flag only: rejected to keep parity between MCP + CLI flows and avoid forgetting to gate CI; env toggle allows repo‑wide control with per-call overrides.

## Phases

### Phase 1 — Shared HTTP client, config, and server wiring
**Goal:** Real HTTP delivery path exists behind env/parameter gate, and FastMCP `notify_mobile` can execute it with structured logging.

**Changes**
- Code: `src/notifier_server/http_client.py` — implement async helper with retry/backoff, timeout, response parsing, request ID support, and token redaction helpers.
- Code: `src/notifier_server/config.py` — add new settings (`NOTIFY_MAX_RETRIES`, `NOTIFY_TIMEOUT_SECONDS`, `NOTIFY_ENABLE_LIVE_SEND`, `NOTIFY_REQUEST_ID_PREFIX`), derived defaults, and validation for positive ints/bools.
- Code: `src/notifier_server/server.py` — add `live_send` arg (default `settings.enable_live_send`), branch to HTTP helper when enabled, capture success/failure text, surface actionable error strings, and emit structured logs with sanitized response bodies.
- Tests: `tests/test_http_client.py` — new suite mocking `httpx.AsyncClient` or `httpx.MockTransport` for success, retriable failures, 4xx stop conditions, jitter/backoff, timeout propagation, and token redaction.
- Tests: `tests/test_server.py` — extend to ensure `notify_mobile` passes headers/body into helper, respects `live_send=False`, redacts tokens in logs, and maps HTTP result strings correctly.
- Config/Docs: `.env.example`, `docs/setup/env-vars.md` — document new env vars, defaults, and how they interact with CLI flags; mention disabling live send for CI.

**Notes**
- Gate all network calls behind `NOTIFY_ENABLE_LIVE_SEND` (default true locally, false in CI examples) and maintain `live_send=False` path for tests/dry-run.
- Add dependency injection hooks so tests can pass a stub transport/backoff scheduler without hitting real network.

**Success Criteria**  
**Automated**
- [ ] Build/typecheck passes: `uv run python -m src.notifier_server.server --check`
- [ ] Unit tests pass: `uv run pytest tests/test_http_client.py -q`
- [ ] Lint/style passes: `make lint`
- [ ] Integration/E2E (server-level): `uv run pytest tests/test_server.py::test_notify_mobile_live_send -q`
- [ ] Formatting check: `make format`
**Manual**
- [ ] Run `make dev` with `NOTIFY_ENABLE_LIVE_SEND=false` and confirm logs report “dry run” messaging without errors.
- [ ] Temporarily point `NTFY_BASE_URL` at a mock server (e.g., `pytest-httpserver`) and verify structured log lines include `event=notify_mobile`, `topic`, `priority`, `request_id`, and sanitized token snippets.
- [ ] Confirm failure path when tokens are invalid returns a user-friendly summary string without leaking secrets.

---

### Phase 2 — CLI helper execution path & test coverage
**Goal:** `scripts/send_test_notification.py` can execute real HTTP sends with overrides while reusing the shared helper, and tests exercise CLI + helper integrations.

**Changes**
- Code: `scripts/send_test_notification.py` — wire `--execute` to `live_send=True`, add `--retries`, `--timeout`, `--request-id-prefix`, rework output to summarize HTTP status + snippet, and reuse shared redaction/logging helpers.
- Code: `src/notifier_server/http_client.py` — expose synchronous wrapper or helper to build payloads from CLI arguments to avoid duplication.
- Tests: `tests/test_cli_send_notification.py` (new) — unit test argparse + behavior (dry-run prints reminder, execute path calls HTTP helper with overrides, redaction on log/print), using `pytest` monkeypatch & `capsys`.
- Tests: extend `tests/test_http_client.py` with coverage for CLI-supplied overrides (e.g., custom timeout) and verifying request IDs attach as expected.
- Tooling: add `make notify:test-live` target invoking script with `--execute` + env toggles for easier manual testing, updating `Makefile`.

**Notes**
- Preserve backward compatibility: default remains dry-run unless `--execute` or env flag is set; script exits non-zero on HTTP failure for easier CI gating.
- Ensure CLI logs friendly troubleshooting hints on common HTTP status codes (401/403/429/5xx) and surfaces `Retry-After` header when present.

**Success Criteria**  
**Automated**
- [ ] Build/typecheck passes: `uv run python -m src.notifier_server.server --check`
- [ ] Unit tests pass: `uv run pytest tests/test_cli_send_notification.py -q`
- [ ] Lint/style passes: `make lint`
- [ ] Integration/E2E (script): `uv run pytest tests/test_http_client.py::test_send_notification_cli_override -q`
- [ ] Formatting check: `make format`
**Manual**
- [ ] Run `uv run python scripts/send_test_notification.py --message "Live test" --execute` against a real ntfy topic to confirm delivery.
- [ ] Run same command with `--timeout 1 --retries 5` against an invalid token and confirm failure summary plus retry log entries.
- [ ] Documented `make notify:test-live` path works end-to-end and prints sanitized headers.

---

### Phase 3 — Telemetry, docs, troubleshooting, and manual validation polish
**Goal:** Observability, docs, and manual workflows reflect the live-send world with troubleshooting guidance and README telemetry counters.

**Changes**
- Code: `src/notifier_server/server.py` & `scripts/send_test_notification.py` — add structured logging helpers (JSON or key=value) emitting metrics-friendly counters, ensure exceptions are caught/logged with redacted bodies.
- Docs: `README.md` — add “Live send” section covering enabling env vars, summary of structured logging fields/counters, and sample `codex` output expectations.
- Docs: `docs/setup/manual-test-checklist.md` — new steps covering real message verification on ntfy app, toggling env flags, CLI failure induction, and log inspection.
- Docs: `docs/setup/env-vars.md` & `.env.example` — finalize descriptions for new env vars with troubleshooting notes; ensure manual references align with CLI options.
- Docs: new `docs/setup/troubleshooting-ntfy.md` — catalog errors (401, 403, 429, TLS), symptoms, and mitigations referenced from README/checklist.
- Telemetry: optionally add `README` counters table summarizing log fields (e.g., `notifications.sent`, `notifications.failed`) and instructions for tailing logs.

**Notes**
- Keep logging output easy to parse locally (key=value) but note how to switch to JSON via an env var if contributors prefer structured logs.
- Provide remediation guidance for dry-run vs live-run mismatches and document how to disable live sends in CI or forks.

**Success Criteria**  
**Automated**
- [ ] Build/typecheck passes: `uv run python -m src.notifier_server.server --check`
- [ ] Unit tests pass: `uv run pytest -q`
- [ ] Lint/style passes: `make lint`
- [ ] Integration/E2E (docs validation via spell/lint if applicable) or `make format`
- [ ] Formatting check: `make format`
**Manual**
- [ ] Follow updated manual checklist to send a notification via Codex FastMCP (live) and confirm ntfy mobile/web apps receive it.
- [ ] Induce a 403 by using an invalid token and verify structured logs + troubleshooting doc lead to resolution.
- [ ] Confirm README telemetry counters/logging section accurately reflects live behavior and redaction.

---

## Testing Strategy
- **Unit tests:** Expand coverage in `tests/test_http_client.py` for retryable statuses, `Retry-After` handling, jitter bounds, timeout propagation, and token/request-ID redaction. Add CLI tests verifying argparse defaults, overrides, and exit codes. Extend `tests/test_server.py` with cases for `live_send=True/False`, structured log payloads, and response messaging when helper raises.
- **Integration tests:** Use `httpx.MockTransport` to simulate ntfy responses for both server and CLI entry points, ensuring `X-Request-ID` headers propagate and retries honor exponential backoff. Consider adding a lightweight fixture that asserts logs include sanitized headers.
- **Manual/E2E:** Updated checklist instructs running `make dev` + Codex CLI to confirm real notifications land, plus failure scenarios (invalid token, forced timeout) to validate user-facing errors. Document verifying `make notify:test-live`.
- **Observability validation:** Add tests ensuring log helper always redacts tokens and clamps response body snippets to 200 chars.

## Performance & Security
- Default budgets: 5s timeout, 3 retries with capped exponential backoff per spec; expose env overrides and log when hitting retry limits. Measure HTTP duration via log timestamps. Ensure Authorization tokens are never logged raw; `_redact_token` is applied on success/failure paths. Use HTTPS enforcement already present in config and add TLS error guidance in troubleshooting doc. Optionally support `httpx.AsyncClient` connection pooling for reuse.

## Migration & Rollback
- Feature flag: `NOTIFY_ENABLE_LIVE_SEND` defaults to true locally but can be set false in CI or `.env` to keep dry runs. `notify_mobile` accepts `live_send=False` for tests. Rollback path is to set env flag false or revert to stub helper while leaving CLI/dcos intact. Document fallback in README/troubleshooting (e.g., how to disable live sends quickly if ntfy outages occur).
- Config migration: `.env.example` and docs instruct contributors to add new env vars; provide defaults so existing `.env` files stay valid without immediate edits. Tests covering missing env var fallback reduce risk.

## Risks & Mitigations
- **Accidental live sends in CI or forks** → Default env flag to false in CI docs, highlight toggle in README, and ensure tests set `live_send=False`.
- **Token leakage via logging/tracebacks** → Centralize redaction helper, add regression tests verifying tokens never appear in logs even during exceptions.
- **Retry storms against ntfy** → Respect `Retry-After`, cap retries/backoff, log warnings when limits hit, and allow CLI overrides for debugging.
- **Contributor confusion toggling live/dry** → Provide CLI flags + env docs + manual checklist updates; default script to dry-run unless `--execute` is set.
- **Network dependency flakiness** → Provide dry-run fallback, mention `NOTIFY_TIMEOUT_SECONDS`, and document troubleshooting steps for TLS/firewall issues.

## Timeline & Owners (optional)
- Phase 1 (HTTP client & server): ~1.0 engineering day — Owner: Core platform engineer.
- Phase 2 (CLI + tests): ~0.75 engineering day — Owner: same engineer or tooling specialist.
- Phase 3 (Telemetry/docs/manual): ~0.75 engineering day — Owner: engineer + doc contributor.

## References
- Spec: `docs/specs/2025-11-25-live-ntfy-delivery.md`
- Research: `docs/research/2025-11-19-live-ntfy-delivery-research.md`
- Existing code/docs mentioned:
  - `src/notifier_server/server.py:97`
  - `src/notifier_server/config.py:34`
  - `scripts/send_test_notification.py:21`
  - `tests/test_server.py:29`
  - `README.md:1`
  - `.env.example:3`
  - `docs/setup/env-vars.md:1`
  - `docs/setup/manual-test-checklist.md:1`
