from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from kira_server.providers.config import ProviderConfig, ProviderConfigStore, remember_secret

ProviderMode = Literal["auto", "fixture", "real"]


@dataclass(frozen=True)
class ProviderSelection:
    mode: Literal["fixture", "real"]
    source: str
    fixture: str
    config: ProviderConfig | None = None
    metadata: dict[str, Any] | None = None


def select_provider(
    *,
    config_store: ProviderConfigStore,
    provider_mode: ProviderMode = "auto",
    fixture: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    skill_provider: str | None = None,
    skill_model: str | None = None,
) -> ProviderSelection:
    fixture_name = fixture or "welcome"
    if provider_mode == "fixture" or fixture is not None:
        return _fixture_selection(fixture_name, source="fixture")

    selected_provider = provider or skill_provider
    selected_model = model or skill_model
    selected = config_store.get(selected_provider)
    if selected is None and skill_provider and not provider:
        selected_provider = None
        selected = config_store.get(None)
        skill_provider = None
    source = "request_override" if provider or model else ("skill_model_hint" if skill_provider or skill_model else "config")
    if selected is not None and selected_model:
        selected = selected.model_copy(update={"model": selected_model})
    if selected is None:
        return _fixture_selection(fixture_name, source="fallback", fallback_reason="missing_provider_config")
    remember_secret(selected.api_key)
    if not selected.has_api_key:
        return _fixture_selection(
            fixture_name,
            source="fallback",
            fallback_reason="missing_api_key",
            attempted=selected,
            model=selected_model,
        )
    if not selected.base_url or not selected.model:
        return _fixture_selection(
            fixture_name,
            source="fallback",
            fallback_reason="invalid_provider_config",
            attempted=selected,
            model=selected_model,
        )

    return ProviderSelection(
        mode="real",
        source=source,
        fixture=fixture_name,
        config=selected,
        metadata=selected.public_metadata(source=source),
    )


def _fixture_selection(
    fixture: str,
    *,
    source: str,
    fallback_reason: str | None = None,
    attempted: ProviderConfig | None = None,
    model: str | None = None,
) -> ProviderSelection:
    metadata: dict[str, Any] = {
        "mode": "fixture",
        "source": source,
        "fixture": fixture,
    }
    if fallback_reason:
        metadata["fallback_reason"] = fallback_reason
    if attempted:
        metadata["attempted_provider"] = attempted.public_metadata(source="config")
    if model:
        metadata["model"] = model
    return ProviderSelection(mode="fixture", source=source, fixture=fixture, metadata=metadata)
