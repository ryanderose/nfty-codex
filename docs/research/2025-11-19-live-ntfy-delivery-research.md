---
title: "Live ntfy Delivery Spec Research"
date: "2025-11-19 08:57 EST"
researcher: "ChatGPT Codex 5"
question: "What does docs/specs/2025-11-25-live-ntfy-delivery.md specify for the live ntfy milestone?"
scope: "docs/specs/2025-11-25-live-ntfy-delivery.md"
assumptions: ["Spec is authoritative for milestone 2 requirements", "Implementation status is inferred from spec only"]
repository: "ryanderose/nfty-codex"
branch: "master"
commit_sha: "fd9b3c6"
status: "complete"
last_updated: "2025-11-19"
last_updated_by: "ChatGPT Codex 5"
directories_examined: ["docs/specs/"]
tags: ["research", "codebase", "ntfy", "notifications"]
---

# Research: Live ntfy Delivery Spec

**Planning Hand-off (TL;DR)**  
- Milestone 2 targets real ntfy HTTP sends for both the FastMCP `notify_mobile` tool and the CLI helper, keeping dry-run modes for safety.  
- Central HTTP helper, env-configurable retries/timeouts, and redacted structured logging govern reliability and observability.  
- Test matrix spans HTTP success/failure, retry/backoff, and redaction, with manual checklists for live validation and risk mitigations.

## Research Question (from spec)
Document how `docs/specs/2025-11-25-live-ntfy-delivery.md` defines the live ntfy delivery milestone, including behaviors, configuration, testing, and operational safeguards.

## System Overview (what exists today)
The spec frames milestone 2 as the transition from stubbed HTTP calls to true ntfy delivery, coordinated across the FastMCP server (`notify_mobile`) and the CLI test script. It emphasizes a reusable HTTP client, env-driven controls (`enable_live_send`, retry/timeouts), structured telemetry, and both automated/manual validation paths to ensure safe rollout. — `docs/specs/2025-11-25-live-ntfy-delivery.md:3-118` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L3-L118))

## Detailed Findings

### Docs & Decisions
- Objectives require enabling live HTTP delivery, surfacing actionable failure logs, and expanding docs/tests for real-send workflows. — `docs/specs/2025-11-25-live-ntfy-delivery.md:9-26` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L9-L26))
- Deliverables span MCP server logic, CLI behavior, configuration docs, new tests, telemetry polish, and documentation updates. — `docs/specs/2025-11-25-live-ntfy-delivery.md:17-27` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L17-L27))

### Domain & Data
- Core entities include ntfy topics, priorities, categories, and tokens, with responses summarizing status snippets for user feedback. — `docs/specs/2025-11-25-live-ntfy-delivery.md:34-49` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L34-L49))
- Scope limits the system to single-transport, single-shot delivery without provisioning or mobile confirmations. — `docs/specs/2025-11-25-live-ntfy-delivery.md:51-56` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L51-L56))

### Entry Points & Routing
- FastMCP `notify_mobile` tool triggers the server path, toggling real HTTP via `enable_live_send`/`live_send` parameter. — `docs/specs/2025-11-25-live-ntfy-delivery.md:74-79` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L74-L79))
- `scripts/send_test_notification.py` exposes a CLI entry point with `--execute`, `--retries`, and `--timeout` overrides. — `docs/specs/2025-11-25-live-ntfy-delivery.md:80-84` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L80-L84))

### Core Logic
- Dedicated HTTP helper (`src/notifier_server/http_client.py`) standardizes `httpx.AsyncClient` usage, retransmission policy, and optional request IDs. — `docs/specs/2025-11-25-live-ntfy-delivery.md:62-71` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L62-L71))
- Server logic returns friendly success/failure strings and enforces redacted logging around Authorization headers. — `docs/specs/2025-11-25-live-ntfy-delivery.md:74-83` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L74-L83))

### Integrations
- ntfy HTTP API is the sole transport, requiring Authorization tokens, optional `X-Request-ID`, and retry/backoff aligned with ntfy status codes (2xx success, 4xx user errors, 5xx retriable). — `docs/specs/2025-11-25-live-ntfy-delivery.md:34-71` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L34-L71))
- README/troubleshooting updates will teach contributors how to enable live sends safely and interpret ntfy responses. — `docs/specs/2025-11-25-live-ntfy-delivery.md:41-45` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L41-L45))

### Configuration & Secrets
- New env vars govern retries/timeouts (`NOTIFY_MAX_RETRIES`, `NOTIFY_TIMEOUT_SECONDS`), enable live send (`NOTIFY_ENABLE_LIVE_SEND`), and optionally prefix request IDs for tracing. — `docs/specs/2025-11-25-live-ntfy-delivery.md:85-93` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L85-L93))
- Dry-run defaults persist, but docs instruct toggling env vars/CLI flags per environment (CI vs local). — `docs/specs/2025-11-25-live-ntfy-delivery.md:74-93` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L74-L93))

### Tests & Observability
- Automated suite must cover HTTP success/failure, retries, timeout/backoff, redaction, plus new `tests/test_http_client.py`. — `docs/specs/2025-11-25-live-ntfy-delivery.md:24-25,103-109` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L24-L25))
- Manual validation includes CLI live run, MCP-driven send, and induced failure to verify user-facing errors/logging. — `docs/specs/2025-11-25-live-ntfy-delivery.md:112-117` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L112-L117))
- Logging guidance mandates structured key-value output and sanitized response snippets, informing README telemetry docs. — `docs/specs/2025-11-25-live-ntfy-delivery.md:94-99` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L94-L99))

### API/UI Surface (as applicable)
- FastMCP interface continues exposing `notify_mobile`, while CLI script offers `--execute` for real sends and defaults to dry-run to protect contributors lacking credentials. — `docs/specs/2025-11-25-live-ntfy-delivery.md:11-13,74-84` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L11-L84))

## Evidence Log
- Objectives, deliverables, and workflow focus. — `docs/specs/2025-11-25-live-ntfy-delivery.md:9-45` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L9-L45))
- Architecture notes for HTTP helper, server, CLI, and configurations. — `docs/specs/2025-11-25-live-ntfy-delivery.md:62-99` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L62-L99))
- Testing, manual validation, and risk mitigations. — `docs/specs/2025-11-25-live-ntfy-delivery.md:103-126` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L103-L126))
- Timeline, dependencies, and references. — `docs/specs/2025-11-25-live-ntfy-delivery.md:130-142` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L130-L142))

## Code References (Index)
- `docs/specs/2025-11-25-live-ntfy-delivery.md:9-45` — Objectives, deliverables, workflow updates. ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L9-L45))
- `docs/specs/2025-11-25-live-ntfy-delivery.md:62-99` — HTTP helper, server/CLI behavior, logging. ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L62-L99))
- `docs/specs/2025-11-25-live-ntfy-delivery.md:103-134` — Testing regimen, manual steps, risks, timeline. ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L103-L134))

## Architecture & Patterns (as implemented)
A layered approach is described: FastMCP tool and CLI defer to a shared HTTP client that centralizes retry/backoff logic, token handling, request IDs, and redacted structured logging. Env-driven toggles (`NOTIFY_ENABLE_LIVE_SEND`, request ID prefix) plus CLI flags let each entry point switch between dry-run and live send modes while emitting consistent observability data. — `docs/specs/2025-11-25-live-ntfy-delivery.md:62-99` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L62-L99))

## Related Documentation
- Initial scaffolding spec referenced for background. — `docs/specs/2025-11-25-live-ntfy-delivery.md:5,138-141` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L5-L141))
- ntfy API publishing docs provide external integration reference. — `docs/specs/2025-11-25-live-ntfy-delivery.md:142` ([permalink](https://github.com/ryanderose/nfty-codex/blob/fd9b3c6/docs/specs/2025-11-25-live-ntfy-delivery.md#L142))

## Open Questions
- How is the shared HTTP client wired into existing modules today? (Would inspect `src/notifier_server/` to confirm module boundaries once implemented.)
- What structured logging format (JSON vs key-value) is chosen in actual code? (Review logging configuration files or README telemetry sections once updated.)

## Follow-up
None at this time.
