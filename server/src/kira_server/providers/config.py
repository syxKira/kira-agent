from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

MINIMAX_GLOBAL_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_GLOBAL_PRESET = "Minimax Global"
DEFAULT_CONFIG_PATH = Path.home() / ".kira-agent" / "config.yaml"
CONFIG_PATH_ENV = "KIRA_CONFIG_PATH"
REDACTED = "[redacted]"


class RetryConfig(BaseModel):
    attempts: int = Field(default=1, ge=0, le=5)
    backoff_seconds: float = Field(default=0.2, ge=0, le=10)


class ProviderConfig(BaseModel):
    name: str = "default"
    provider: str = "openai"
    preset: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    timeout: float = Field(default=30.0, gt=0, le=300)
    retry: RetryConfig = Field(default_factory=RetryConfig)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "baseURL" in normalized and "base_url" not in normalized:
            normalized["base_url"] = normalized["baseURL"]
        return normalized

    @model_validator(mode="after")
    def apply_preset(self) -> "ProviderConfig":
        if self.preset == MINIMAX_GLOBAL_PRESET:
            self.provider = "openai"
            self.base_url = self.base_url or MINIMAX_GLOBAL_BASE_URL
        if self.provider is None:
            self.provider = "openai"
        return self

    @property
    def has_api_key(self) -> bool:
        return bool((self.api_key or "").strip())

    def public_metadata(self, *, source: str, fallback_reason: str | None = None) -> dict[str, Any]:
        metadata = {
            "mode": "real",
            "source": source,
            "provider": self.provider,
            "name": self.name,
            "preset": self.preset,
            "model": self.model,
            "base_url": redact_url(self.base_url),
            "api_key": redact_api_key(self.api_key),
            "has_api_key": self.has_api_key,
        }
        if fallback_reason:
            metadata["fallback_reason"] = fallback_reason
        return {key: value for key, value in metadata.items() if value is not None}


class ProviderConfigStore(BaseModel):
    default_provider: str | None = None
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    config_path: str
    loaded: bool = False
    error: str | None = None

    def get(self, name: str | None) -> ProviderConfig | None:
        if name:
            return self.providers.get(name)
        if self.default_provider:
            return self.providers.get(self.default_provider)
        if self.providers:
            return next(iter(self.providers.values()))
        return None

    def readiness_metadata(self) -> dict[str, Any]:
        return {
            "loaded": self.loaded,
            "config_path": self.config_path,
            "default_provider": self.default_provider,
            "providers": {
                name: provider.public_metadata(source="config") for name, provider in self.providers.items()
            },
            "error": redact_text(self.error) if self.error else None,
        }


def config_path_from_env() -> Path:
    override = os.environ.get(CONFIG_PATH_ENV)
    return Path(override).expanduser() if override else DEFAULT_CONFIG_PATH


def load_provider_config(path: Path | None = None) -> ProviderConfigStore:
    config_path = path or config_path_from_env()
    if not config_path.exists():
        return ProviderConfigStore(config_path=str(config_path), loaded=False)

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        providers, default_provider = _parse_provider_config(raw)
        return ProviderConfigStore(
            default_provider=default_provider,
            providers=providers,
            config_path=str(config_path),
            loaded=True,
        )
    except Exception as exc:
        return ProviderConfigStore(
            config_path=str(config_path),
            loaded=False,
            error=f"{type(exc).__name__}: {redact_text(str(exc))}",
        )


def _parse_provider_config(raw: dict[str, Any]) -> tuple[dict[str, ProviderConfig], str | None]:
    if not isinstance(raw, dict):
        raise ValueError("provider config must be a mapping")

    providers_raw = raw.get("providers")
    default_provider = raw.get("default_provider") or raw.get("defaultProvider")
    providers: dict[str, ProviderConfig] = {}
    if isinstance(providers_raw, dict):
        for name, value in providers_raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"provider {name} must be a mapping")
            providers[name] = ProviderConfig.model_validate({"name": name, **value})
        return providers, default_provider or (next(iter(providers)) if providers else None)

    provider_data = {
        key: value
        for key, value in raw.items()
        if key not in {"default_provider", "defaultProvider", "providers"}
    }
    if provider_data:
        name = str(default_provider or raw.get("name") or "default")
        providers[name] = ProviderConfig.model_validate({"name": name, **provider_data})
        return providers, name
    return providers, None


def minimax_global_preset() -> ProviderConfig:
    return ProviderConfig(
        name="minimax-global",
        preset=MINIMAX_GLOBAL_PRESET,
        provider="openai",
        base_url=MINIMAX_GLOBAL_BASE_URL,
    )


def redact_api_key(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return REDACTED
    return f"{value[:3]}...{value[-4:]}"


def redact_url(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("api_key=", "api_key=[redacted]&")


def redact_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value
    for provider in _known_secret_values:
        if provider:
            text = text.replace(provider, REDACTED)
    return re.sub(r"sk-[A-Za-z0-9._-]+", REDACTED, text)


_known_secret_values: set[str] = set()


def remember_secret(value: str | None) -> None:
    if value:
        _known_secret_values.add(value)
