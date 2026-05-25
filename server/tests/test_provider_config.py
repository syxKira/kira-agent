from __future__ import annotations

from pathlib import Path

from kira_server.providers.config import (
    CONFIG_PATH_ENV,
    MINIMAX_GLOBAL_BASE_URL,
    MINIMAX_GLOBAL_PRESET,
    config_path_from_env,
    load_provider_config,
    minimax_global_preset,
    redact_api_key,
    redact_text,
    remember_secret,
)


def test_default_config_path_is_used(monkeypatch) -> None:
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)

    path = config_path_from_env()

    assert path.name == "config.yaml"
    assert path.parent.name == ".kira-agent"


def test_config_path_override_is_used(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("model: test-model\nbaseURL: https://example.test/v1\napi_key: sk-secret\n", encoding="utf-8")
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config))

    store = load_provider_config()

    provider = store.get(None)
    assert store.loaded is True
    assert store.config_path == str(config)
    assert provider is not None
    assert provider.provider == "openai"
    assert provider.base_url == "https://example.test/v1"
    assert provider.model == "test-model"


def test_minimax_global_preset() -> None:
    provider = minimax_global_preset()

    assert provider.preset == MINIMAX_GLOBAL_PRESET
    assert provider.provider == "openai"
    assert provider.base_url == MINIMAX_GLOBAL_BASE_URL


def test_config_with_minimax_and_custom_provider(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        """
default_provider: minimax
providers:
  minimax:
    preset: Minimax Global
    model: MiniMax-Text-01
    api_key: sk-minimax-secret
  custom:
    baseURL: https://custom.example/v1
    model: custom-model
    api_key: sk-custom-secret
""",
        encoding="utf-8",
    )

    store = load_provider_config(config)

    assert store.default_provider == "minimax"
    assert store.providers["minimax"].base_url == MINIMAX_GLOBAL_BASE_URL
    assert store.providers["custom"].provider == "openai"
    assert store.providers["custom"].base_url == "https://custom.example/v1"


def test_invalid_config_reports_redacted_error(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("- not-a-mapping\n", encoding="utf-8")

    store = load_provider_config(config)

    assert store.loaded is False
    assert store.error is not None
    assert "provider config must be a mapping" in store.error


def test_redaction_helpers_hide_secrets() -> None:
    remember_secret("sk-very-secret-value")

    assert redact_api_key("sk-very-secret-value") == "sk-...alue"
    assert redact_text("failed with sk-very-secret-value") == "failed with [redacted]"
