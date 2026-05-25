from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from kira_server.core.events import ProviderEvent
from kira_server.main import create_app
from kira_server.providers.base import ProviderRequest
from kira_server.providers.config import ProviderConfig, ProviderConfigStore
from kira_server.providers.selection import select_provider


def config_store(api_key: str | None = "sk-secret") -> ProviderConfigStore:
    return ProviderConfigStore(
        default_provider="default",
        config_path="/tmp/config.yaml",
        loaded=True,
        providers={
            "default": ProviderConfig(
                name="default",
                provider="openai",
                base_url="https://example.test/v1",
                model="model-a",
                api_key=api_key,
            ),
            "other": ProviderConfig(
                name="other",
                provider="openai",
                base_url="https://other.example/v1",
                model="model-b",
                api_key=api_key,
            ),
        },
    )


def test_provider_selection_config_default_and_overrides() -> None:
    default = select_provider(config_store=config_store())
    provider_override = select_provider(config_store=config_store(), provider="other")
    model_override = select_provider(config_store=config_store(), model="model-c")
    fixture = select_provider(config_store=config_store(), provider_mode="fixture", fixture="welcome")

    assert default.mode == "real"
    assert default.config is not None
    assert default.config.model == "model-a"
    assert default.metadata["api_key"] != "sk-secret"
    assert provider_override.config is not None
    assert provider_override.config.name == "other"
    assert provider_override.source == "request_override"
    assert model_override.config is not None
    assert model_override.config.model == "model-c"
    assert fixture.mode == "fixture"


def test_provider_selection_missing_key_falls_back_to_fixture() -> None:
    selection = select_provider(config_store=config_store(api_key=None))

    assert selection.mode == "fixture"
    assert selection.metadata["fallback_reason"] == "missing_api_key"
    assert "sk-secret" not in json.dumps(selection.metadata)


class FakeOpenAIProvider:
    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        yield ProviderEvent(type="text_delta", data={"text": "remote"})
        yield ProviderEvent(type="done", data={"message": "done"})


def test_run_uses_real_provider_and_redacted_metadata() -> None:
    fake = FakeOpenAIProvider()
    client = TestClient(create_app(fixture_delay_seconds=0, provider_config=config_store(), openai_provider=fake))

    run_response = client.post("/api/runs", json={"prompt": "hello"}).json()
    with client.stream("GET", run_response["events_url"]) as stream_response:
        payloads = _read_sse_payloads(stream_response.iter_lines())

    assert run_response["provider"]["mode"] == "real"
    assert run_response["provider"]["model"] == "model-a"
    assert "sk-secret" not in json.dumps(run_response)
    assert fake.requests[0].config is not None
    assert fake.requests[0].config.api_key == "sk-secret"
    assert [payload["type"] for payload in payloads] == ["text_delta", "done"]
    assert payloads[0]["data"]["provider"]["mode"] == "real"
    assert "sk-secret" not in json.dumps(payloads)


def test_provider_status_is_redacted() -> None:
    client = TestClient(create_app(fixture_delay_seconds=0, provider_config=config_store()))

    response = client.get("/api/provider/status")

    assert response.status_code == 200
    assert "sk-secret" not in json.dumps(response.json())
    assert response.json()["providers"]["default"]["api_key"] != "sk-secret"


def _read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads
