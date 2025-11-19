---
title: "Initial Build Scaffolding Research"
date: "2025-11-18 23:36 EST"
researcher: "ChatGPT Codex 5"
question: "Document the current state of the ntfy notification workflow repository per the 2025-11-20 scaffolding spec."
scope: "Entire workspace (docs/initial-spec, docs/specs); repo currently contains only specification files."
assumptions: ["Repository intentionally lacks code per scaffolding spec statement that it is currently empty", "Initial codex→ntfy workflow spec is the authoritative behavioral reference"]
repository: "/Users/ryanderose/code/nfty-codex"
branch: "master"
commit_sha: "580bddc"
status: "complete"
last_updated: "2025-11-18"
last_updated_by: "ChatGPT Codex 5"
directories_examined: ["docs/", "docs/initial-spec/", "docs/specs/"]
tags: ["research", "codebase", "docs", "notifications", "scaffolding"]
---

# Research: Initial Build Scaffolding Research

**Planning Hand-off (TL;DR)**  
- Repository contents are limited to the initial ntfy workflow spec and the scaffolding supplement, which explicitly call out that the repo is currently empty and awaiting the described structure (`docs/specs/2025-11-20-initial-build-scaffolding.md:5-58`).  
- The scaffolding spec enumerates every deliverable (target directories, MCP server stub, config helpers, developer tooling, validation assets) and their responsibilities so collaborators know exactly where future files will live (`docs/specs/2025-11-20-initial-build-scaffolding.md:18-140`).  
- The primary workflow spec defines the `notify_mobile` tool contract, ntfy HTTP payload rules, environment configuration, Codex CLI wiring, and testing/operational expectations (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:7-482`).

## Research Question (from spec)
Capture what already exists in this repository (even if only documentation) for the Codex → ntfy notification workflow and explain how the specified components are intended to interact at this stage.

## Spec Snapshot
- **Objectives**: Stand up repository scaffolding, ship a stub FastMCP server exposing `notify_mobile`, and provide docs/scripts/config to unblock further work (`docs/specs/2025-11-20-initial-build-scaffolding.md:9-29`).
- **Domain terms**: Codex CLI/IDE host, FastMCP server, ntfy topic/app, notification workflow semantics (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:7-124`).
- **Entry points**: Planned `src/notifier_server/server.py` with `FastMCP` registration and `notify_mobile` tool, plus Codex configuration via `[mcp_servers.codex-notifier]` (`docs/specs/2025-11-20-initial-build-scaffolding.md:70-78`; `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:243-304`).
- **Integrations**: ntfy HTTP endpoint (base URL, topic, auth token), Codex CLI stdio transport, ntfy mobile/web client subscription steps (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:182-338`).
- **Entities**: `ConfigSettings` module encapsulating env vars (`NTFY_BASE_URL`, `NTFY_TOPIC`, `NTFY_TOKEN`, priority defaults) and `PRIORITY_MAP` conversion table (`docs/specs/2025-11-20-initial-build-scaffolding.md:55-88`).
- **Risks**: Misconfigured topics or TOML can break Codex integrations, ntfy topics must stay high-entropy, and MCP servers run outside Seatbelt/Landlock (trust boundary) (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:300-425`; `docs/specs/2025-11-20-initial-build-scaffolding.md:55-58`).

## System Overview (what exists today)
The repository contains only documentation: `docs/initial-spec/2025-11-18-codex-ntfy-spec.md` captures the end-to-end workflow design, and `docs/specs/2025-11-20-initial-build-scaffolding.md` narrows that into a concrete scaffolding checklist. There is no `src/`, `scripts/`, or tooling yet; the scaffolding spec itself notes the repo is currently empty while defining the target directories/API contracts (`docs/specs/2025-11-20-initial-build-scaffolding.md:5-58,31-53`). A file inventory confirms only the two spec files are tracked at commit `580bddc`:

```
$ rg --files
docs/specs/2025-11-20-initial-build-scaffolding.md
docs/initial-spec/2025-11-18-codex-ntfy-spec.md
```

## Detailed Findings

### Docs & Decisions
- Two authored specs drive all knowledge: the initial workflow requirements (architecture, behavior, security) and the implementation scaffolding deliverables, with explicit cross-links between them (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:7-482`; `docs/specs/2025-11-20-initial-build-scaffolding.md:5-157`).

### Domain & Data
- Domain entities are configuration-centric: `ConfigSettings` should aggregate ntfy connection fields, enforce non-empty topic, validate HTTPS base URL, and provide a `PRIORITY_MAP` for translating human priorities into ntfy integers (`docs/specs/2025-11-20-initial-build-scaffolding.md:55-88`).
- Ntfy messages must omit secrets/code, stay short, allow optional category tags, and optionally add repo context only when `include_repo` is true (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:157-180`).

### Entry Points & Routing
- The planned entrypoint is `src/notifier_server/server.py`, instantiating a `FastMCP` app named `codex-notifier`, registering `notify_mobile`, and exposing `server.run()` for both CLI execution and Codex-managed use (`docs/specs/2025-11-20-initial-build-scaffolding.md:70-79`).
- Codex consumes this server via stdio as configured in `[mcp_servers.codex-notifier]` within `~/.codex/config.toml`, using `uv run` with required dependencies and an absolute script path (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:243-272`).

### Core Logic
- `notify_mobile` accepts a status `message`, optional `title`, `priority`, `category`, and `include_repo` flag, enforcing when-to-use guidance that targets long-running completions or blocking failures, while guarding against frequent low-value calls (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:139-180`).
- Implementation phases are already prescribed: validate inputs, load configuration, assemble/log the ntfy payload using `httpx.AsyncClient` but stub the actual POST unless configuration is complete, and uniformly handle exceptions by returning text responses (`docs/specs/2025-11-20-initial-build-scaffolding.md:70-78`).

### Integrations
- Outbound integration is ntfy’s HTTP API: default base URL `https://ntfy.sh`, per-topic endpoints, priority/tag headers, optional bearer token, and expectation of async HTTP to avoid blocking Codex (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:182-210,387-398`).
- Client-side integration covers ntfy mobile/web subscription instructions and encouragement to self-host or secure tokens for sensitive deployments (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:307-338,414-420`).

### Configuration & Secrets
- `.env` support plus `docs/setup/env-vars.md` are mandated to document `NTFY_*` fields; `.env.example` must include placeholders and cautionary comments (`docs/specs/2025-11-20-initial-build-scaffolding.md:55-111`).
- Runtime validation should error politely when `NTFY_TOPIC` is missing, normalize invalid priorities, and allow overriding default priorities via `NOTIFY_DEFAULT_PRIORITY` (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:211-228`).

### Tests & Observability
- Logging levels are prescribed (INFO for outbound payload summaries, WARNING for config issues, ERROR for failures) and must remain local to the machine (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:229-238`).
- Validation artifacts include a manual test checklist, sample Codex config, and a `send_test_notification.py` script; completion criteria cite `uv run ...` smoke tests, linting, and verifying Codex lists the tool (`docs/specs/2025-11-20-initial-build-scaffolding.md:91-140`).
- Operational tests stress manual Codex calls to `notify_mobile` and long-running task scenarios to ensure single notification semantics (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:430-451`).

### API/UI Surface (as applicable)
- The exposed API surface is a single MCP tool `notify_mobile` with the exact signature shown in the spec along with docstring/prompt guidance controlling usage and message contents (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:141-180`).
- Codex’s user-facing configuration snippet demonstrates how the tool appears in `~/.codex/config.toml`, clarifying command/args structure for CLI and VS Code clients alike (`docs/initial-spec/2025-11-18-codex-ntfy-spec.md:243-259`).

## Evidence Log
- `docs/specs/2025-11-20-initial-build-scaffolding.md:5-58` (commit 580bddc) — Repository context, objectives, and statement that it is currently empty.
- `docs/specs/2025-11-20-initial-build-scaffolding.md:18-111` (commit 580bddc) — Deliverables, directory layout, config/docs/tooling requirements.
- `docs/specs/2025-11-20-initial-build-scaffolding.md:114-140` (commit 580bddc) — Codex config snippet expectations and validation checklist.
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:7-124` (commit 580bddc) — Background, architecture, and component definitions.
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:139-238` (commit 580bddc) — Tool contract, HTTP integration details, configuration/logging behaviors.
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:243-451` (commit 580bddc) — Codex config instructions, ntfy client setup, functional requirements, and testing guidance.
- Command `rg --files` (repo root, commit 580bddc) — Only the two spec files exist at this time.

## Code References (Index)
- `docs/specs/2025-11-20-initial-build-scaffolding.md:18-111` — Defines target filesystem layout, modules, scripts, and documentation assets for the first implementation.
- `docs/specs/2025-11-20-initial-build-scaffolding.md:70-88` — Specifies the FastMCP server entrypoint responsibilities and configuration helper design.
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:139-210` — Details tool signature, permitted parameters, and ntfy HTTP payload contract.
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:243-304` — Shows Codex config snippet and usage expectations for the MCP server.
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:307-451` — Documents ntfy client setup, functional requirements, and test procedures.

## Architecture & Patterns (as implemented)
The documented architecture follows a three-tier flow: Codex CLI/IDE hosts the FastMCP server over stdio, the server exposes a single `notify_mobile` tool encapsulating validation/config lookups, and outgoing notifications call ntfy via HTTPS to reach subscribed mobile/web clients. The scaffolding keeps config handling centralized (`config.py`), enforces one-notification-per-task semantics, and relies on `uv` to supply reproducible Python environments (`docs/specs/2025-11-20-initial-build-scaffolding.md:31-88`; `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:110-210,243-338`).

## Related Documentation
- `docs/initial-spec/2025-11-18-codex-ntfy-spec.md:7-482` — Authoritative Codex → ntfy workflow specification.
- `docs/specs/2025-11-20-initial-build-scaffolding.md:5-157` — Initial build/scaffolding instructions derived from the main spec.

## Open Questions
- None — maintainers confirmed all deliverables enumerated in the scaffolding spec (source tree, scripts, setup docs) will be created within this initial build project (`docs/specs/2025-11-20-initial-build-scaffolding.md:31-111`).

## Follow-up (append only, as needed)
- [2025-11-18 23:36 EST] Initial documentation-only state captured for commit 580bddc.
- [2025-11-18 23:42 EST] Maintainer clarified that every artifact listed in the scaffolding spec will land in this project, resolving earlier open questions.
