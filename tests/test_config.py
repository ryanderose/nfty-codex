from __future__ import annotations

import pytest

from notifier_server import config


TEST_ENV_VARS = [
    "NTFY_BASE_URL",
    "NTFY_TOPIC",
    "NTFY_TOKEN",
    "NOTIFY_DEFAULT_PRIORITY",
    "NOTIFY_DEFAULT_CATEGORY",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path_factory):
    override_env = tmp_path_factory.mktemp("env") / ".env"
    override_env.write_text("", encoding="utf-8")
    monkeypatch.setenv("NOTIFIER_ENV_FILE", str(override_env))
    for key in TEST_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    config.reset_settings_cache()
    yield
    config.reset_settings_cache()


def test_load_settings_from_env(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "  codex-notify-demo  ")
    monkeypatch.setenv("NTFY_BASE_URL", "https://example.com/prefix/")
    monkeypatch.setenv("NOTIFY_DEFAULT_PRIORITY", "HIGH")

    loaded = config.load_settings()

    assert loaded.ntfy_topic == "codex-notify-demo"
    assert loaded.ntfy_base_url == "https://example.com/prefix"
    assert loaded.default_priority == "high"


def test_invalid_priority_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "demo-topic")
    monkeypatch.setenv("NOTIFY_DEFAULT_PRIORITY", "invalid")

    loaded = config.load_settings()

    assert loaded.default_priority == "default"


def test_missing_topic_raises_validation_error(monkeypatch):
    monkeypatch.delenv("NTFY_TOPIC", raising=False)

    with pytest.raises(config.ValidationError):
        config.load_settings()


def test_default_category_normalization(monkeypatch):
    monkeypatch.setenv("NTFY_TOPIC", "topic")
    monkeypatch.setenv("NOTIFY_DEFAULT_CATEGORY", "  tests  ")

    loaded = config.load_settings()

    assert loaded.default_category == "tests"


def test_env_file_is_respected(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("NTFY_TOPIC=test-from-env\n", encoding="utf-8")
    monkeypatch.setenv("NOTIFIER_ENV_FILE", str(env_file))
    config.reset_settings_cache()

    loaded = config.load_settings()

    assert loaded.ntfy_topic == "test-from-env"
