from __future__ import annotations

import pytest

from notifier_server import config
from notifier_server.server import notify_mobile, main

ENV_VARS = [
    "NTFY_BASE_URL",
    "NTFY_TOPIC",
    "NTFY_TOKEN",
    "NOTIFY_DEFAULT_PRIORITY",
    "NOTIFY_DEFAULT_CATEGORY",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path_factory):
    temp_env = tmp_path_factory.mktemp("env") / ".env"
    temp_env.write_text("", encoding="utf-8")
    monkeypatch.setenv("NOTIFIER_ENV_FILE", str(temp_env))
    for key in ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    config.reset_settings_cache()
    yield
    config.reset_settings_cache()


@pytest.mark.asyncio
async def test_notify_mobile_success(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "demo")
    response = await notify_mobile("All done", priority="high", category="tests")

    assert "demo" in response
    assert "stubbed" in response


@pytest.mark.asyncio
async def test_notify_mobile_handles_invalid_priority(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "demo")
    response = await notify_mobile("status", priority="invalid")

    assert "falling back" in response
    assert "default" in response


@pytest.mark.asyncio
async def test_notify_mobile_config_error(monkeypatch):
    monkeypatch.delenv("NTFY_TOPIC", raising=False)

    response = await notify_mobile("hello")

    assert "configuration error" in response


def test_main_check_success(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "demo")
    assert main(["--check"]) == 0


def test_main_check_failure(monkeypatch):
    monkeypatch.delenv("NTFY_TOPIC", raising=False)
    assert main(["--check"]) == 1
