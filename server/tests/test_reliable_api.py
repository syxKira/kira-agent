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
from kira_server.storage.database import RuntimeDatabase, RuntimeStorage


class CountingProvider:
    def __init__(self, events: list[ProviderEvent] | None = None) -> None:
        self.events = events or [
            ProviderEvent(type="text_delta", data={"text": "remote"}),
            ProviderEvent(type="done", data={"message": "done"}),
        ]
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        for event in self.events:
            yield event


def test_graph_run_state_replay_and_cursor_do_not_rerun_provider(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    provider = CountingProvider()
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=provider,
            skill_registry=create_builtin_skill_registry(),
            runtime_storage=storage,
        )
    )

    run = client.post("/api/runs", json={"prompt": "hello", "skill_id": TEST_SKILL_ID}).json()
    with client.stream("GET", run["events_url"]) as response:
        events = _read_sse_payloads(response.iter_lines())
    replay = client.get(f"/api/runs/{run['thread_id']}/replay").json()
    state = client.get(f"/api/runs/{run['thread_id']}/state").json()
    with client.stream("GET", f"{run['events_url']}?after_seq=1") as response:
        replayed = _read_sse_payloads(response.iter_lines())

    assert [event["seq"] for event in events] == [1, 2, 3]
    assert state["latest_seq"] == 3
    assert state["status"] == "completed"
    assert state["checkpoints"]
    assert replay["events"][0]["data"]["text"] == "remote"
    assert [event["seq"] for event in replayed] == [2, 3]
    assert len(provider.requests) == 1


def test_reliable_state_unknown_run_and_terminal_resume(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    client = TestClient(create_app(fixture_delay_seconds=0, runtime_storage=storage))

    missing = client.get("/api/runs/missing/state")

    assert missing.status_code == 404
    run = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    resume = client.post(f"/api/runs/{run['thread_id']}/resume")
    assert resume.status_code == 409
    assert resume.json()["detail"]["code"] == "terminal_run"


def test_cancelled_run_remains_inspectable(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    client = TestClient(create_app(fixture_delay_seconds=0, runtime_storage=storage))

    run = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    cancelled = client.post(f"/api/runs/{run['thread_id']}/cancel")
    state = client.get(f"/api/runs/{run['thread_id']}/state")

    assert cancelled.status_code == 200
    assert state.status_code == 200
    assert state.json()["status"] == "cancelled"
    assert state.json()["failure_class"] == "cancelled"


def test_repair_notes_and_unsafe_repair_rejection(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    client = TestClient(create_app(fixture_delay_seconds=0, runtime_storage=storage))

    run = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    ok = client.post(f"/api/runs/{run['thread_id']}/repair-notes", json={"note": "checked state"})
    unsafe = client.post(f"/api/runs/{run['thread_id']}/repair-notes", json={"note": "api_key sk-secret"})
    replay = client.get(f"/api/runs/{run['thread_id']}/replay").json()

    assert ok.status_code == 200
    assert unsafe.status_code == 400
    dumped = json.dumps(replay)
    assert "checked state" in dumped
    assert "sk-secret" not in dumped


def test_graph_tool_result_is_ledgered_and_reused(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=CountingProvider(),
            skill_registry=create_builtin_skill_registry(),
            runtime_storage=storage,
        )
    )

    first = client.post(
        "/api/runs",
        json={"prompt": "please use project tool", "skill_id": TEST_SKILL_ID, "project_root": str(tmp_path)},
    ).json()
    with client.stream("GET", first["events_url"]) as response:
        events = _read_sse_payloads(response.iter_lines())
    state = client.get(f"/api/runs/{first['thread_id']}/state").json()

    assert any(event["type"] == "tool_result" for event in events)
    assert state["side_effects"][0]["status"] == "completed"
    assert state["side_effects"][0]["idempotency_key"]


def test_provider_failure_class_and_redaction(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    provider = CountingProvider([ProviderEvent(type="error", data={"code": "provider_retry_exhausted", "message": "failed sk-secret"})])
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=config_store(),
            openai_provider=provider,
            skill_registry=create_builtin_skill_registry(),
            runtime_storage=storage,
        )
    )

    run = client.post("/api/runs", json={"prompt": "hello", "skill_id": TEST_SKILL_ID}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    state = client.get(f"/api/runs/{run['thread_id']}/state").json()

    assert state["status"] == "error"
    assert state["failure_class"] == "provider_stream_error"
    assert state["provider_attempts"][-1]["status"] == "error"
    assert "sk-secret" not in json.dumps(state)


def config_store() -> ProviderConfigStore:
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
                api_key="sk-secret",
            )
        },
    )


def _read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads
