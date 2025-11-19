# Spec: Live ntfy Delivery & Telemetry Polish

Version 0.1 — 2025-11-25

This spec defines the second milestone for the Codex → ntfy notification project. Building on the initial scaffolding (see `docs/specs/2025-11-20-initial-build-scaffolding.md`), the goal is to move from a stubbed HTTP workflow to a fully operational pipeline that can send real notifications while preserving safety, observability, and developer experience.

---

## 1. Objectives

1. Enable live ntfy HTTP delivery from both the FastMCP `notify_mobile` tool and the `scripts/send_test_notification.py` helper, while keeping a dry-run option for contributors who lack credentials.
2. Add logging, redaction, and error-handling improvements so Codex users see actionable messages when delivery fails.
3. Extend automated tests and docs to cover real-send workflows, including configuration guidance and troubleshooting.

---

## 2. Deliverables Overview

| Area | Deliverable |
| --- | --- |
| MCP server | Real HTTP POST/PUT logic (with retries/backoff) gated by `enable_live_send` flag |
| CLI script | `--execute` flag that performs a real ntfy call; dry-run remains default |
| Configuration | New env vars for retry tuning (`NOTIFY_MAX_RETRIES`, `NOTIFY_TIMEOUT_SECONDS`) documented in `docs/setup/env-vars.md` + `.env.example` |
| Testing | `tests/test_server.py` + new `tests/test_http_client.py` mocking `httpx.AsyncClient` to cover success/failure, retry, redaction |
| Telemetry | Structured logging (event type, topic, priority, request_id) plus summary counters in README |
| Documentation | Updated README/manual checklist/troubleshooting for live sends, plus new spec (this doc) |

---

## 3. Scope & Non-Goals

### In Scope

- Implement real ntfy HTTP request logic within `notify_mobile` and the helper script, including:
  - Configurable timeout & retry/backoff (default 5s timeout, 3 attempts, exponential backoff with jitter).
  - Token injection via Authorization header, masking in logs.
  - Handling HTTP status codes (2xx success, 4xx user error, 5xx retry).
  - Optional `X-Request-ID` header for correlation.
- Provide meaningful responses to Codex: success message when POST succeeds, friendly error message summarizing failure cause (status + snippet).
- Add integration-friendly logging: JSON structured logs or key-value logs with fields `topic`, `priority`, `category`, `include_repo`, `request_id`, `result`.
- Update developer workflows:
  - README instructions for enabling live send, running dry-run vs execute.
  - Manual checklist additions for verifying real notifications (web app + mobile).
  - Troubleshooting doc snippet for common ntfy errors (401, 403, 429, TLS issues).
- Expand tests to cover:
  - HTTP success path (mock `httpx.AsyncClient` to return 200).
  - HTTP error path with retries & final failure messaging.
  - Timeout/backoff behavior (use `pytest` `monkeypatch` or `httpx.MockTransport`).
  - Logging redaction ensures tokens never appear in logs even when exceptions occur.

### Out of Scope

- Multi-transport support (only ntfy for now).
- Scheduling / queueing of notifications (one shot per request).
- Mobile confirmation or two-way communication.
- Automated provisioning of ntfy topics or tokens.

---

## 4. Architecture & Implementation Notes

### 4.1 HTTP Client Layer

- Introduce a dedicated helper (e.g., `src/notifier_server/http_client.py`) to encapsulate HTTP operations and retries. This ensures both the MCP server and CLI script reuse the same logic.
- Use `httpx.AsyncClient` with `timeout=Timeout(read=timeout, write=timeout, connect=timeout)`; enable `follow_redirects=False`.
- Retry policy:
  - Reattempt on network errors and HTTP statuses 500, 502, 503, 504.
  - Stop immediately on 4xx unless 429 (retry with exponential backoff).
  - Backoff formula: `min(base * 2**attempt + jitter, max_backoff)`.
- Provide optional `NOTIFY_REQUEST_ID` env var toggle to include `X-Request-ID` header for better tracing.

### 4.2 Server Behavior

- `notify_mobile` should:
  - Validate inputs as before.
  - Build the payload and call the HTTP helper if `enable_live_send` is true (default `True` once this milestone lands). Add a `live_send` parameter (default `True`) for testing.
  - For tests/dry-run, set `live_send=False` to skip HTTP.
  - On success: return `"Notification sent to topic '<topic>' with priority '<p>'."`
  - On failure: return `"Failed to send notification (status 403): Unauthorized – check NTFY_TOKEN."` or similar, plus log structured error.
- `scripts/send_test_notification.py`:
  - Add `--execute` flag (already present but currently stubbed) that flips `live_send=True`.
  - When `--execute` is passed, call the shared HTTP helper; on success print the response status/body snippet.
  - Provide `--retries`, `--timeout` CLI overrides for power users (default to env-configured values).

### 4.3 Configuration Additions

- `.env.example` / `docs/setup/env-vars.md` new entries:
  - `NOTIFY_MAX_RETRIES` (default 3)
  - `NOTIFY_TIMEOUT_SECONDS` (default 5)
  - `NOTIFY_ENABLE_LIVE_SEND` (default `true`; useful for dry-run-only environments)
  - `NOTIFY_REQUEST_ID_PREFIX` (optional string to help trace requests; append random suffix per send)
- Document interplay between flags and CLI options; mention that CI/test environments can set `NOTIFY_ENABLE_LIVE_SEND=false` to avoid network calls.

### 4.4 Observability & Logging

- Standard log format: `[LEVEL] event=notify_mobile topic=<topic> priority=<priority> request_id=<id> status=<status|error>`
- When HTTP succeeds, log status code and response headers summary.
- On failure, log status/error and include sanitized snippet of response body (limit to 200 chars, remove newline).
- Provide guidance in README for tailing logs, enabling JSON logging via env var (optional).

---

## 5. Testing & Validation

### Automated

1. `uv run pytest -q` covering new modules/tests.
2. `uv run pytest tests/test_server.py::test_notify_mobile_live_send` (new) ensures HTTP helper is invoked with expected headers.
3. `make lint` and `make format`.
4. `uv run python -m src.notifier_server.server --check` still validates env settings.

### Manual

1. Configure `.env` with real ntfy topic/token.
2. Run `uv run python scripts/send_test_notification.py --message "Live test" --execute` and confirm a real notification arrives (web app or mobile).
3. Start `make dev`, add the MCP config, and from Codex ask it to send a notification; confirm ntfy receives it and logs show a successful HTTP call with redacted token.
4. Trigger a failure (e.g., set bad token) and confirm Codex sees a friendly error plus logs highlight the issue.

---

## 6. Risks & Mitigations

- **Accidental live sends in CI**: default to live enabled but document toggling via `NOTIFY_ENABLE_LIVE_SEND=false`; add guard in tests to force dry-run.
- **Token leakage**: ensure all logging paths use redaction helper; add unit tests verifying redaction even when exceptions occur.
- **Retry storms**: cap retries/backoff, log warnings when repeated failures happen, and surface `Retry-After` header if present.
- **User confusion**: update docs/checklist with explicit “dry-run vs execute” guidance.

---

## 7. Timeline & Dependencies

- Estimated effort: ~2-3 engineering days.
- Dependencies: existing scaffold repo, ntfy topic/token for manual verification.
- Blocking issues: none (assuming network access to ntfy).

---

## 8. References

- Initial scaffolding spec: `docs/specs/2025-11-20-initial-build-scaffolding.md`
- Workflow reference: `docs/initial-spec/2025-11-18-codex-ntfy-spec.md`
- ntfy API docs: https://docs.ntfy.sh/publish/

