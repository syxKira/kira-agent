from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

from kira_server.core.events import ProviderEvent
from kira_server.main import create_app
from kira_server.providers.base import ProviderRequest
from kira_server.providers.config import ProviderConfig, ProviderConfigStore
from kira_server.skills.builtin import TEST_SKILL_ID, create_builtin_skill_registry


class FakeOpenAIProvider:
    def __init__(self, events: list[ProviderEvent] | None = None) -> None:
        self.events = events or [
            ProviderEvent(type="thinking_delta", data={"text": "remote thinking"}),
            ProviderEvent(type="text_delta", data={"text": "remote visible"}),
            ProviderEvent(type="done", data={"message": "done"}),
        ]
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        for event in self.events:
            yield event


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


def test_skill_graph_run_streams_model_and_tool_events(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=create_builtin_skill_registry(),
        )
    )

    run = client.post(
        "/api/runs",
        json={"prompt": "please use project tool", "skill_id": TEST_SKILL_ID, "project_root": str(tmp_path)},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())

    assert run["skill"]["skill_id"] == TEST_SKILL_ID
    assert run["provider"]["mode"] == "real"
    assert fake.requests[0].config is not None
    assert fake.requests[0].config.api_key == "sk-secret"
    assert [payload["type"] for payload in payloads] == ["thinking_delta", "text_delta", "tool_start", "tool_result", "checkpoint", "done"]
    assert payloads[3]["data"]["name"] == "list_project_files"
    assert payloads[-1]["data"]["skill"]["skill_id"] == TEST_SKILL_ID
    assert "sk-secret" not in json.dumps(run)
    assert "sk-secret" not in json.dumps(payloads)


def test_skill_graph_fixture_fallback_when_key_missing() -> None:
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(api_key=None),
            skill_registry=create_builtin_skill_registry(),
        )
    )

    run = client.post("/api/runs", json={"prompt": "hello", "skill_id": TEST_SKILL_ID}).json()
    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())

    assert run["provider"]["mode"] == "fixture"
    assert run["provider"]["fallback_reason"] == "missing_api_key"
    assert payloads[0]["data"]["provider"]["mode"] == "fixture"
    assert payloads[-1]["type"] in {"done", "error"}


def test_skill_graph_provider_and_model_overrides_reach_provider() -> None:
    fake = FakeOpenAIProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=create_builtin_skill_registry(),
        )
    )

    run = client.post(
        "/api/runs",
        json={"prompt": "hello", "skill_id": TEST_SKILL_ID, "provider": "other", "model": "override-model"},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())

    assert run["provider"]["source"] == "request_override"
    assert run["provider"]["model"] == "override-model"
    assert fake.requests[0].config is not None
    assert fake.requests[0].config.name == "other"
    assert fake.requests[0].model == "override-model"
    assert payloads[0]["data"]["provider"]["model"] == "override-model"


def test_no_skill_fixture_and_provider_paths_remain_available() -> None:
    fake = FakeOpenAIProvider([ProviderEvent(type="text_delta", data={"text": "direct"}), ProviderEvent(type="done", data={})])
    provider_client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=create_builtin_skill_registry(),
        )
    )
    fixture_client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=create_builtin_skill_registry(),
        )
    )

    provider_run = provider_client.post("/api/runs", json={"prompt": "hello"}).json()
    fixture_run = fixture_client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    with provider_client.stream("GET", provider_run["events_url"]) as response:
        provider_payloads = _read_sse_payloads(response.iter_lines())
    with fixture_client.stream("GET", fixture_run["events_url"]) as response:
        fixture_payloads = _read_sse_payloads(response.iter_lines())

    assert [payload["type"] for payload in provider_payloads] == ["text_delta", "done"]
    assert [payload["type"] for payload in fixture_payloads] == [
        "thinking_delta",
        "text_delta",
        "text_delta",
        "text_delta",
        "done",
    ]


def test_skill_graph_runtime_error_streams_structured_error() -> None:
    fake = FakeOpenAIProvider([ProviderEvent(type="error", data={"code": "provider_timeout", "message": "timeout"})])
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=fake,
            skill_registry=create_builtin_skill_registry(),
        )
    )

    run = client.post("/api/runs", json={"prompt": "hello", "skill_id": TEST_SKILL_ID}).json()
    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())

    assert [payload["type"] for payload in payloads] == ["error"]
    assert payloads[0]["data"]["code"] == "provider_timeout"


def _read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads
