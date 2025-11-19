# Manual Test Checklist

Use this checklist after completing the automated validation for each phase. It wires together the `.env` configuration, the MCP server, and Codex CLI so you can verify notifications end-to-end.

- [ ] **Prepare environment file**
  - Copy `.env.example` to `.env`.
  - Fill in `NTFY_TOPIC`, optional `NTFY_BASE_URL`, and `NTFY_TOKEN` if your topic is private.
  - Confirm the ntfy mobile/web client is already subscribed to the topic.
- [ ] **Install dependencies**
  - Run `make setup` (wraps `uv sync`).
  - Confirm `uv run ruff --version` and `uv run pytest -q` both succeed.
- [ ] **Validate configuration**
  - Run `uv run python -m src/notifier_server.server --check`.
  - Ensure it reports the topic/base URL you configured without errors.
- [ ] **Start the MCP server**
  - Start it via `make dev` (runs `uv run python -m src.notifier_server.server`).
  - Keep the process running in a dedicated terminal pane; expect INFO logs describing payloads.
- [ ] **Run the notification script**
  - Execute `make notify:test` which wraps `scripts/send_test_notification.py --message "Codex manual test" --dry-run`.
  - Confirm it prints a JSON blob showing the URL, headers, and body along with a reminder that HTTP execution is stubbed. Authorization headers must be redacted.
- [ ] **Register Codex MCP server**
  - Append the block from `README.md` to `~/.codex/config.toml` (replace the script path with your repo path):
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
  - Restart Codex CLI / the VS Code extension.
  - Run `codex tools` (or `codex --list-tools`) and confirm `notify_mobile` is listed.
- [ ] **Trigger a notification via Codex**
  - In a Codex session ask: “Notify my phone when the test suite is done.”
  - Let Codex complete a long-running task and confirm your ntfy client shows the stubbed response (it will mention that HTTP delivery is currently stubbed).

Do not check off any of the boxes above until you have manually completed the step on your workstation.
