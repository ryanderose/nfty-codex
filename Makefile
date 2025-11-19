UV ?= uv
PYTHON ?= $(UV) run python

.PHONY: setup dev lint format notify\:test

setup:
	$(UV) sync

dev:
	$(UV) run python -m src.notifier_server.server

lint:
	$(UV) run ruff check src scripts

format:
	$(UV) run ruff format src scripts

notify\:test:
	$(UV) run python scripts/send_test_notification.py --message "Codex scaffold test" --dry-run
