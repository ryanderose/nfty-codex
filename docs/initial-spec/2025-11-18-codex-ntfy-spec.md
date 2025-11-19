# Spec: Codex CLI → Phone Notifications via MCP + Ntfy (“Nifty / NFTY app” workflow)

Version 0.9 — Draft  

---

## 1. Purpose & Scope

This spec defines how to implement an **asynchronous notification workflow** for **OpenAI Codex CLI** using:

- **Codex CLI** as the *agent host*  
- A **Python MCP server** (FastMCP-based) as the *notification tool*  
- **ntfy.sh** (“Nifty / NFTY app”: mobile + web clients) as the *transport*  

When Codex finishes long-running or critical work (e.g., full test runs, big refactors), it will **semantically decide** to call the MCP tool, which in turn will send a push notification to the user’s phone via ntfy.

This spec covers:

- Architecture & data flow  
- Detailed behavior of the MCP notification tool  
- Codex CLI integration (including config.toml, approval modes, sandbox implications)  
- Ntfy topic & app setup  
- Security / privacy and operational considerations  

---

## 2. Background: Codex CLI & Latency

### 2.1 Codex CLI Overview

Codex CLI is a **local-first, agentic coding assistant** that runs in your terminal and can also be used from the Codex IDE extension. It inspects your repo, edits files, and runs shell commands with varying degrees of autonomy.

Key points relevant to this project:

- **Local execution**: Code and commands run on the user’s machine; source does *not* leave the environment except via explicit actions.  
- **Sandboxing** (Seatbelt on macOS, Landlock on Linux) limits raw shell access; Codex prefers controlled, tool-based integrations.  
- **Approval modes** (conceptual):  
  - *Suggest*: human approves every change.  
  - *Auto-Edit*: auto file edits; shell commands need approval.  
  - *Full Auto*: fully autonomous within the repo.  
- **Configuration**:  
  - Single shared config file at `~/.codex/config.toml` (or `%USERPROFILE%\.codex\config.toml` on Windows).  
  - Same file is used by **Codex CLI** and the **VS Code Codex extension**.  

### 2.2 Codex + MCP

Codex can connect to **MCP servers** via **stdio transport**, configured in `config.toml` under `[mcp_servers.<name>]`.

Facts we rely on:

- Codex acts as an **MCP host**; it spawns each MCP server process and talks JSON-RPC over stdin/stdout.  
- Supported transport (as of late 2025): **local stdio servers only**; remote SSE/HTTP requires a proxy.  
- MCP configuration is shared between CLI and IDE; misconfigured TOML can break both.  

This makes MCP the correct mechanism for a **trusted, semantic integration** like notifications.

---

## 3. Goals & Non‑Goals

### 3.1 Goals

1. **Mobile notifications for Codex tasks**  
   - Get a phone push when Codex finishes long or critical work *without* babysitting the terminal.

2. **Semantic triggering**  
   - Notification should be sent when Codex *understands* it’s appropriate (e.g., test suite done, refactor complete, critical error), not merely when the process exits.

3. **Minimal friction**  
   - Implementation should be **simple to install and maintain**:  
     - No Java daemons, headless browsers, or custom mobile apps.  
     - One Python MCP server, one ntfy topic + mobile app.

4. **Shared between CLI & IDE**  
   - Same MCP tool available inside **Codex CLI** and **Codex VS Code extension** via shared `config.toml`.

5. **Security-aware**  
   - No source code or secrets are sent in notifications by default.  
   - Encourages self-hosted ntfy for sensitive environments.

### 3.2 Non‑Goals

- Two-way mobile control (replying to notifications to steer Codex).  
- A generic notification broker supporting many transports (Pushover, Telegram, etc.)—those are possible extensions.  
- High-volume alerting; this is intended for **low-frequency, high-value** notifications.

---

## 4. System Architecture

### 4.1 Components

1. **Codex CLI / Codex IDE extension**
   - Acts as MCP host.  
   - Runs agents and decides when to call tools based on instructions and tool descriptions.

2. **Notification MCP Server (Python)**
   - Implemented using **FastMCP**, the official Python SDK’s high-level server utility.  
   - Exposes a single tool, e.g. `notify_mobile`.

3. **ntfy.sh / ntfy server**
   - HTTP-based pub/sub system where each **topic** is a channel.  
   - Notification is a single HTTP POST/PUT to `https://ntfy.sh/<topic>` (or self-hosted base URL) with headers for title, priority, tags, etc.  

4. **Ntfy Mobile / Web App (“Nifty / NFTY app”)**
   - Official ntfy Android/iOS apps or the web app (`ntfy.sh/app`).  
   - User subscribes to the chosen topic (e.g. `codex_<UUID>`).  
   - Displays notifications as standard OS push notifications.

### 4.2 High-Level Flow

1. User launches Codex in a repo and asks it to perform a long-running task.  
2. Codex plans and executes work (edits files, runs tests, etc.).  
3. When it **finishes a long-running or critical operation**, Codex calls the MCP tool `notify_mobile` with a short status message and urgency.  
4. MCP server sends HTTP request to ntfy topic.  
5. ntfy sends a push to the subscribed mobile (or web) client.  
6. User receives notification and chooses whether to return to Codex.

### 4.3 Sequence (Textual)

- Codex host ↔ MCP server: JSON-RPC over stdio  
- MCP server ↔ ntfy server: HTTPS POST  
- ntfy server ↔ mobile app: APNS/FCM/OS push (handled fully by ntfy)

---

## 5. Detailed Design

### 5.1 Notification MCP Server

#### 5.1.1 Tech Stack

- **Language**: Python 3.11+  
- **Environment manager**: `uv` (fast Python package + env manager).  
- **Libraries**:  
  - `mcp` (Python SDK, including FastMCP server class).  
  - `httpx` for async HTTP calls to ntfy.  

#### 5.1.2 Tool Definition

Tool name (example): `notify_mobile`

Signature:

```python
@mcp.tool()
async def notify_mobile(
    message: str,
    title: str = "Codex task status",
    priority: str = "default",
    category: str | None = None,
    include_repo: bool = False,
) -> str:
    ...
```

Semantics (docstring – acts as tool’s prompt):

- When to use:
  - After **long-running tasks** (builds, full tests, large refactors).  
  - On **critical errors** blocking progress and requiring user attention.  
  - When **explicitly requested** by user (“notify me on my phone when this finishes”).  
- When *not* to use:
  - Trivial or very fast operations.  
  - Frequent progress updates (avoid spamming phone).

Content rules:

- Must **not include raw source code or secrets**.  
- Message should be a **short, high-level status summary**, for example:
  - `"Full test suite passed (124 tests) on branch feature/analytics"`  
  - `"Migrations failed: database timeout connecting to staging"`  

Parameters behavior:

- `message` (required): concise sentence or two.  
- `title`: short label for notification (maps to ntfy `Title` header).  
- `priority`: one of `min`, `low`, `default`, `high`, `urgent` mapped to ntfy priorities.  
- `category` (optional): descriptive tag (e.g. `tests`, `deploy`, `refactor`) → ntfy `Tags` header.  
- `include_repo`: if `True`, allow including repo name or branch, but still no code.

#### 5.1.3 Ntfy HTTP Integration

- **Base URL** (configurable):  
  - Default: `https://ntfy.sh` (public service).  
  - Optional: self-hosted instance URL via environment variable.

- **Topic**:
  - High-entropy string, e.g. UUID-style: `codex-notify-8d0b2e4a-...`  
  - Provided via env var `NTFY_TOPIC`; no sensible default to avoid collisions.

- **HTTP request**:

```python
url = f"{base_url.rstrip('/')}/{topic}"
headers = {
    "Title": title,
    "Priority": priority,
    "Tags": ",".join(tags),  # e.g. ["codex", category, urgency-level]
}
resp = await client.post(url, data=message, headers=headers)
```

- Error handling:
  - If HTTP status ≥ 400: log and return `"Failed to send notification: <error>"` to Codex.  
  - MCP tool **must not crash**; always return a string (Codex will surface it to the user).

- Optional auth:
  - If `NTFY_TOKEN` env var is set, send header `Authorization: Bearer <token>` for authenticated topics.  

#### 5.1.4 Configuration (Environment)

Environment variables read by the MCP server:

- `NTFY_BASE_URL` (optional): e.g. `https://ntfy.mycorp.internal`  
- `NTFY_TOPIC` (required): topic name string  
- `NTFY_TOKEN` (optional): bearer token for authenticated topic  
- `NOTIFY_DEFAULT_PRIORITY` (optional): override `"default"`  

Behavior if misconfigured:

- Missing `NTFY_TOPIC`:  
  - MCP tool returns `"Notification not sent: NTFY_TOPIC not configured"` and logs warning.  
- HTTP/network errors:  
  - Log error, return `"Failed to send notification: <error>"`.  
- Invalid priority:  
  - Normalize to `"default"` and attach warning in return string.

#### 5.1.5 Logging

- Use Python `logging` module.  
- Log levels:
  - INFO: outbound notifications (topic, priority, truncated message).  
  - WARNING: configuration problems.  
  - ERROR: HTTP/network failures or unexpected exceptions.

The logs remain local to machine and are not transmitted.

---

### 5.2 Codex CLI Integration

#### 5.2.1 MCP Server Registration in `config.toml`

User (or installer) must edit `~/.codex/config.toml` to register the MCP server.

Example block:

```toml
[mcp_servers.codex-notifier]
command = "uv"
args = [
  "run",
  "--with", "mcp[cli]",
  "--with", "httpx",
  "/absolute/path/to/notification_server.py"
]
```

Key points:

- `command = "uv"`: let `uv` manage Python env and dependencies.  
- `args`:
  - `run`: runs the script in an ephemeral environment.  
  - `--with mcp[cli] --with httpx`: ensures required packages are installed.  
  - Script path must be **absolute**, since Codex may be launched from any directory.  

Config considerations:

- Keep TOML syntax correct; a malformed `[mcp_servers]` table can break all MCP integrations in Codex CLI *and* VS Code.  
- After editing `config.toml`, user must restart Codex.

#### 5.2.2 Codex Behavior / Usage Pattern

In practice:

- User might start Codex via:  
  - `codex` (interactive TUI) or  
  - `codex exec "Run full test suite on this repo"` for automation mode.  

- Codex learns tool semantics from `notify_mobile` description:  
  - For **short tasks**, Codex should usually *not* call the tool.  
  - For **long-running tasks**, Codex is encouraged to call `notify_mobile` once at completion or terminal failure.  
  - When user explicitly says **“Notify me on my phone when you’re done”**, Codex should *always* call it.

To reinforce this, include a note in the Codex **session/system prompt** or AGENTS.md (if you use that pattern) like:

> When tasks are long-running or critical, call the `notify_mobile` tool with a short summary once at the end of the task so the user’s phone gets an ntfy notification. Do not spam the tool for quick or trivial actions.

Approval modes context:

- **Suggest mode**:  
  - Notifications less critical; user is already approving each step.  
  - Still useful if tests are slow or user walks away.  

- **Auto-Edit / Full Auto**:  
  - Notification tool is most valuable here.  
  - Codex may run for minutes; user often leaves terminal window.  

Sandbox implications:

- MCP server is **not** running under Codex’s strict sandbox; it runs under normal user permissions because the user explicitly configured it.  
- This is powerful but requires the MCP server code to be trusted.

---

### 5.3 Ntfy Client Setup (“Nifty / NFTY app”)

#### 5.3.1 Topic Choice

- Generate a high-entropy topic, e.g. using `uuidgen`:
  - Example: `codex-notify-4e0363d3-7f5f-4e6a-9c55-9d6c2b1e7bd4`  
- Configure this string in:
  - MCP server env: `NTFY_TOPIC`  
  - ntfy app subscription: same topic string.

This avoids **topic hijacking** (others guessing your channel).  

#### 5.3.2 Mobile App

Steps:

1. Install **ntfy** app on mobile (Google Play, F-Droid, or App Store).  
2. Open app → **Add Subscription**.  
3. Enter topic string (e.g. `codex-notify-...`).  
4. Optionally, set custom notification sound per topic.

Alternatively, user can use **web app** at `ntfy.sh/app` and subscribe to the same topic; browser notifications will fire.  

#### 5.3.3 Self-Hosted Option

For privacy-sensitive deployments:

- Run self-hosted ntfy server via Docker or system package.  
- Configure:
  - `NTFY_BASE_URL` to internal URL.  
  - Optionally enable authentication and use `NTFY_TOKEN`.

---

## 6. Functional Requirements

### FR‑1: Send Notification on Long-Running Completion

When Codex finishes a task that took **longer than a human-attention threshold** (approx. multi-minute operations, determined semantically by the model), it **should** call `notify_mobile` with:

- Message summarizing outcome (success/failure + key metrics).  
- Priority: `default` (or `high` if explicitly asked by the user).  
- Category: `tests`, `build`, `refactor`, etc.

### FR‑2: Notify on Critical Errors

If Codex encounters a **blocking error** (e.g., failing migrations, repeated build failures, environment misconfigurations), it **should** call `notify_mobile` with:

- Priority: `high` or `urgent` when the error requires immediate manual intervention.  
- Message: high-level summary (“Integration tests failing consistently due to missing DB credentials”).

### FR‑3: Honor Explicit User Requests

When user says things like:

- “Ping my phone when the test suite is done.”  
- “Notify me on my phone if this fails.”

Codex **must** use `notify_mobile` once the relevant task completes or fails.

### FR‑4: Single Notification per Task

To avoid spam:

- For a single long-running task, **at most one notification** should be issued (plus optional explicit failure notification when there is a clear, separate failure event).

### FR‑5: Safe Content

Notification content **must not include**:

- Raw source code lines  
- Stack traces with secrets  
- API keys, tokens, passwords, connection strings  

Notifications should be short, human-readable summaries.

---

## 7. Non-Functional Requirements

- **Reliability**
  - MCP server should **not crash** Codex even if ntfy is unreachable.  
  - All exceptions are caught and turned into textual errors returned to Codex.

- **Performance**
  - HTTP call to ntfy must be asynchronous; it must not block Codex’s main loop significantly.  
  - Codex doesn’t need to wait for confirmation to continue work.

- **Portability**
  - Works on macOS, Linux, and Windows (as long as Python + uv are available).  
  - No OS-specific dependencies in the MCP server.

- **Config Safety**
  - `config.toml` modifications should be minimal and well-documented.  
  - If MCP server misbehaves, user can comment out `[mcp_servers.codex-notifier]` and restart Codex.

---

## 8. Security & Privacy

### 8.1 Data Minimization

- MCP tool description and docs must stress: **no code, no secrets** in messages.  
- For extra safety, tool could enforce:
  - Message length limit (e.g., 256–512 chars).  
  - Simple regex checks to block obvious key patterns (e.g., common API key prefixes).

### 8.2 Ntfy Topic Security

- Public ntfy relies on obscurity of topic strings; hence high-entropy topics are required.  
- For corporate environments:
  - Prefer **self-hosted** ntfy with auth tokens.  
  - Use HTTPS and internal routing only.

### 8.3 Trust Boundary

- Codex sandbox restricts arbitrary network calls, but MCP servers run as **trusted external processes**, with full user permissions.  
- Review the MCP server code, and store it in a version-controlled repo.

---

## 9. Operational Procedures

### 9.1 Installation Steps (High-Level)

1. **Install Codex CLI** and ensure it’s working.  
2. **Install uv** (stand-alone or via package manager).  
3. **Create notification MCP project**:
   - New directory with `notification_server.py`.  
   - Include MCP + httpx dependencies.  
4. **Edit `~/.codex/config.toml`** to add `[mcp_servers.codex-notifier]` block using `uv run`.  
5. **Set environment variables**: `NTFY_BASE_URL`, `NTFY_TOPIC`, `NTFY_TOKEN` (if needed).  
6. **Install ntfy app** on phone and subscribe to topic.  
7. Restart Codex and confirm that the `notify_mobile` tool is visible in its tool list.

### 9.2 Testing

- Manual MCP test:
  - In Codex, ask explicitly:  
    > “Call the `notify_mobile` tool with a message saying ‘Test notification from Codex’ and high priority.”  
  - Verify phone receives push.

- Long-running task test:
  - Ask Codex to run full test suite or a large refactor.  
  - Ensure it only sends notification once, after completion/failure.

---

## 10. Future Extensions

- **Multiple channels**:  
  - Different topics for `prod`, `staging`, `personal`, etc.  
  - Expose `topic_suffix` parameter in tool and map to `NTFY_TOPIC + "-" + suffix`.

- **Alternative transports**:  
  - Pushover, Telegram MCP servers, or PagerDuty integration for on‑call workflows (similar pattern, different HTTP endpoint and auth).  

- **Bi-directional control** (out of scope now):
  - Use ntfy’s HTTP incoming webhooks or another service to receive replies and forward them into Codex (would likely require a small HTTP server and a mechanism to attach to a running Codex session).

---

## 11. Acceptance Criteria (Summary)

This implementation is considered complete when:

1. **Installation**: A new developer can follow documented steps to install Codex, the MCP notification server, and ntfy app, and get a phone notification quickly.  
2. **Correctness**:  
   - Notifications are sent exactly once at the end of long-running or critical tasks.  
   - Notifications are *not* sent for trivial actions.  
3. **Safety**:  
   - Notifications contain no code or sensitive secrets in normal use.  
4. **Resilience**:  
   - If ntfy is down or misconfigured, Codex continues functioning; errors show up only as textual messages.  
5. **Portability**:  
   - The same MCP config works for both Codex CLI and the VS Code Codex extension via shared `config.toml`.  
