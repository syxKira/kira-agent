from __future__ import annotations

from pathlib import Path

from kira_server.providers.config import (
    APOLLO_APPID_ENV,
    APOLLO_CLUSTER_ENV,
    APOLLO_NS_ENV,
    APOLLO_SECRET_ENV,
    APOLLO_URL_ENV,
    CONFIG_PATH_ENV,
    ENV_PROVIDER_API_KEY,
    ENV_PROVIDER_BASE_URL,
    ENV_PROVIDER_MODEL,
    ENV_PROVIDER_NAME,
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


def test_env_provider_config_is_used_when_file_is_missing(tmp_path: Path, monkeypatch) -> None:
    missing_config = tmp_path / "missing.yaml"
    monkeypatch.setenv(ENV_PROVIDER_NAME, "apollo-provider")
    monkeypatch.setenv(ENV_PROVIDER_BASE_URL, "https://apollo.example/v1")
    monkeypatch.setenv(ENV_PROVIDER_MODEL, "apollo-model")
    monkeypatch.setenv(ENV_PROVIDER_API_KEY, "sk-apollo-secret")

    store = load_provider_config(missing_config)

    provider = store.get(None)
    assert store.loaded is True
    assert store.config_path == str(missing_config)
    assert store.default_provider == "apollo-provider"
    assert provider is not None
    assert provider.provider == "openai"
    assert provider.base_url == "https://apollo.example/v1"
    assert provider.model == "apollo-model"
    assert provider.has_api_key is True


def test_file_provider_config_takes_precedence_over_env(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("model: file-model\nbaseURL: https://file.example/v1\napi_key: sk-file-secret\n", encoding="utf-8")
    monkeypatch.setenv(ENV_PROVIDER_NAME, "apollo-provider")
    monkeypatch.setenv(ENV_PROVIDER_BASE_URL, "https://apollo.example/v1")
    monkeypatch.setenv(ENV_PROVIDER_MODEL, "apollo-model")
    monkeypatch.setenv(ENV_PROVIDER_API_KEY, "sk-apollo-secret")

    store = load_provider_config(config)

    provider = store.get(None)
    assert store.loaded is True
    assert provider is not None
    assert provider.base_url == "https://file.example/v1"
    assert provider.model == "file-model"


def test_apollo_provider_config_is_used_when_file_and_env_are_missing(tmp_path: Path, monkeypatch) -> None:
    missing_config = tmp_path / "missing.yaml"
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return (
                b'{"KIRA_PROVIDER_NAME":"apollo-provider",'
                b'"KIRA_PROVIDER_BASE_URL":"https://apollo.example/v1",'
                b'"KIRA_PROVIDER_MODEL":"apollo-model",'
                b'"KIRA_PROVIDER_API_KEY":"sk-apollo-secret"}'
            )

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers.get("Authorization")
        captured["timestamp"] = request.headers.get("Timestamp")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("kira_server.providers.config.urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("kira_server.providers.config.time.time", lambda: 1234.567)
    monkeypatch.setenv(APOLLO_URL_ENV, "https://apollo.example")
    monkeypatch.setenv(APOLLO_APPID_ENV, "3121")
    monkeypatch.setenv(APOLLO_CLUSTER_ENV, "18822.staging.SHA")
    monkeypatch.setenv(APOLLO_NS_ENV, "application")
    monkeypatch.setenv(APOLLO_SECRET_ENV, "apollo-secret")

    store = load_provider_config(missing_config)

    provider = store.get(None)
    assert store.loaded is True
    assert provider is not None
    assert provider.base_url == "https://apollo.example/v1"
    assert provider.model == "apollo-model"
    assert provider.has_api_key is True
    assert captured["url"] == "https://apollo.example/configfiles/json/3121/18822.staging.SHA/application"
    assert captured["authorization"].startswith("Apollo 3121:")
    assert captured["timestamp"] == "1234567"
    assert captured["timeout"] == 5


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
