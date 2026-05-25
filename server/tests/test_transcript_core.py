from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

from kira_server.core.events import ProviderEvent
from kira_server.main import create_app
from kira_server.providers.base import ProviderRequest
from kira_server.providers.config import ProviderConfig, ProviderConfigStore
from kira_server.skills.builtin import HITL_FIXTURE_SKILL_ID, create_builtin_skill_registry
from kira_server.storage.database import RuntimeDatabase, RuntimeStorage


class FakeProvider:
    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        yield ProviderEvent(type="thinking_delta", data={"text": "hidden planning"})
        yield ProviderEvent(type="text_delta", data={"text": "visible answer"})
        yield ProviderEvent(type="done", data={"message": "done"})


class ToolOutputProvider(FakeProvider):
    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        yield ProviderEvent(
            type="tool_result",
            data={
                "name": "read_project_file",
                "status": "ok",
                "result": {"text": "alpha " * 600},
            },
        )
        yield ProviderEvent(type="text_delta", data={"text": "tool output handled"})
        yield ProviderEvent(type="done", data={"message": "done"})


class SecretToolOutputProvider(FakeProvider):
    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        yield ProviderEvent(
            type="tool_result",
            data={
                "name": "provider_config_check",
                "status": "ok",
                "result": {"api_key": "sk-secret", "message": "contains sensitive config"},
            },
        )
        yield ProviderEvent(type="done", data={"message": "done"})


def test_run_creates_conversation_and_persists_visible_transcript(tmp_path: Path) -> None:
    client = _client(tmp_path)

    run = client.post("/api/runs", json={"prompt": "hello", "provider_mode": "fixture", "fixture": "welcome"}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    transcript = client.get(f"/api/conversations/{run['conversation_id']}/transcript").json()

    assert run["conversation_id"].startswith("conv_")
    assert run["turn_id"].startswith("turn_")
    assert [message["role"] for message in transcript["messages"][:2]] == ["user", "assistant"]
    dumped = json.dumps(transcript)
    assert "hello" in dumped
    assert "Kira local fixture is running." in dumped
    assert "Preparing local fixture run" not in dumped


def test_follow_up_run_includes_prior_conversation_history(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "hello"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    second = client.post("/api/runs", json={"prompt": "what did I just say?", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{second['thread_id']}/context").json()

    assert second["conversation_id"] == first["conversation_id"]
    assert any(item["kind"] == "conversation_history" and "hello" in item["text"] for item in fake.requests[-1].context_items)
    assert any(item["kind"] == "conversation_history" for item in trace["included"])
    assert trace["transcript"]["conversation_id"] == first["conversation_id"]


def test_manual_compaction_adds_summary_without_deleting_source_messages(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "first goal with approved constraint"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    second = client.post("/api/runs", json={"prompt": "second follow up?", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())

    compact = client.post(f"/api/conversations/{first['conversation_id']}/compact", json={"tail_messages": 1}).json()
    transcript = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()
    context = client.get(f"/api/conversations/{first['conversation_id']}/context").json()

    assert compact["summary"]["summarizer"]["mode"] == "fixture"
    assert compact["summary"]["source_message_ids"]
    assert "first goal" in json.dumps(transcript)
    assert transcript["compaction_summaries"][0]["id"] == compact["summary"]["id"]
    assert any(item["kind"] == "compaction_summary" for item in context["items"])
    assert any(item["reason"] == "covered_by_compaction_summary" for item in context["trace"]["omitted"])


def test_explicit_real_provider_summarizer_uses_redacted_provider_boundary(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "summarize with real provider"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    compact = client.post(
        f"/api/conversations/{first['conversation_id']}/compact",
        json={"summarizer_mode": "real", "tail_messages": 0},
    ).json()

    assert compact["summary"]["summarizer"]["mode"] == "real"
    assert compact["summary"]["summary"] == "visible answer"
    assert "sk-secret" not in json.dumps(compact)


def test_follow_up_context_uses_summary_plus_recent_tail(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "alpha decision must be preserved"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    second = client.post("/api/runs", json={"prompt": "beta recent tail", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    client.post(f"/api/conversations/{first['conversation_id']}/compact", json={"tail_messages": 2})

    follow_up = client.post("/api/runs", json={"prompt": "continue", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", follow_up["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    context_items = fake.requests[-1].context_items

    assert any(item["kind"] == "compaction_summary" and "alpha decision" in item["text"] for item in context_items)
    assert any(item["kind"] == "conversation_history" and "beta recent tail" in item["text"] for item in context_items)
    assert not any(item["kind"] == "conversation_history" and "alpha decision" in item["text"] for item in context_items)


def test_large_tool_output_is_replaced_with_safe_stub_context(tmp_path: Path) -> None:
    provider = ToolOutputProvider()
    client = _client(tmp_path, provider=provider)

    first = client.post("/api/runs", json={"prompt": "read a large output"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    transcript = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()
    replacement = transcript["tool_output_replacements"][0]

    assert replacement["reason"] == "too_large"
    assert replacement["redacted_reference"]["raw_blob"] == "not_exposed_stage_08b"
    assert "alpha " * 100 not in json.dumps(transcript)

    second = client.post("/api/runs", json={"prompt": "what did the tool return?", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())

    assert any(item["kind"] == "tool_summary" and item["metadata"]["source"] == "tool_output_replacement" for item in provider.requests[-1].context_items)
    assert not any("alpha " * 50 in item["text"] for item in provider.requests[-1].context_items)


def test_secret_tool_output_replacement_redacts_raw_values(tmp_path: Path) -> None:
    provider = SecretToolOutputProvider()
    client = _client(tmp_path, provider=provider)

    run = client.post("/api/runs", json={"prompt": "check config"}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    transcript = client.get(f"/api/conversations/{run['conversation_id']}/transcript").json()
    dumped = json.dumps(transcript)

    assert transcript["tool_output_replacements"][0]["reason"] == "secret_guard"
    assert "sk-secret" not in dumped
    assert "api_key" not in dumped


def test_conversations_are_isolated_and_archived_conversation_is_rejected(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)
    first = client.post("/api/runs", json={"prompt": "alpha secret-free note"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    second = client.post("/api/runs", json={"prompt": "new topic"}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())

    assert first["conversation_id"] != second["conversation_id"]
    assert all("alpha secret-free note" not in item.get("text", "") for item in fake.requests[-1].context_items or [])

    archived = client.patch(f"/api/conversations/{first['conversation_id']}", json={"archived": True}).json()["conversation"]
    rejected = client.post("/api/runs", json={"prompt": "continue", "conversation_id": archived["id"]})
    assert rejected.status_code == 404


def test_sse_reconnect_does_not_duplicate_transcript_parts(tmp_path: Path) -> None:
    client = _client(tmp_path)
    run = client.post("/api/runs", json={"prompt": "hello", "provider_mode": "fixture", "fixture": "welcome"}).json()
    with client.stream("GET", run["events_url"]) as response:
        first_payloads = _read_sse_payloads(response.iter_lines())
    first_transcript = client.get(f"/api/conversations/{run['conversation_id']}/transcript").json()
    first_part_count = sum(len(message["parts"]) for message in first_transcript["messages"])

    after_seq = first_payloads[-1]["seq"]
    with client.stream("GET", f"{run['events_url']}?after_seq={after_seq - 1}") as response:
        _read_sse_payloads(response.iter_lines())
    second_transcript = client.get(f"/api/conversations/{run['conversation_id']}/transcript").json()
    second_part_count = sum(len(message["parts"]) for message in second_transcript["messages"])

    assert second_part_count == first_part_count


def test_stage08b_migrations_are_idempotent_and_preserve_transcript(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "kira.db"))
    client = TestClient(create_app(fixture_delay_seconds=0, provider_config=_config_store(), openai_provider=FakeProvider(), runtime_storage=storage))
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "README.md").write_text("indexed project knowledge", encoding="utf-8")
    run = client.post("/api/runs", json={"prompt": "hello"}).json()
    with client.stream("GET", run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    client.post("/api/project/index/refresh", json={"root": str(project_root)})
    memory = client.post(
        "/api/memory",
        json={
            "text": "User prefers compact summaries",
            "scope": "projectLocal",
            "type": "preference",
            "source": {"kind": "manual", "summary": "migration test"},
        },
    ).json()["memory"]

    RuntimeStorage(RuntimeDatabase(tmp_path / "kira.db"))
    state = client.get(f"/api/runs/{run['thread_id']}/state").json()
    project_status = client.get(f"/api/project/index/status?root={project_root}").json()
    memories = client.get("/api/memory?query=compact").json()["memories"]
    transcript = client.get(f"/api/conversations/{run['conversation_id']}/transcript").json()

    assert state["thread_id"] == run["thread_id"]
    assert project_status["file_count"] == 1
    assert any(record["id"] == memory["id"] for record in memories)
    assert "hello" in json.dumps(transcript)
    assert transcript["compaction_summaries"] == []
    assert transcript["tool_output_replacements"] == []


def test_rollback_marks_abandoned_turn_inactive_and_excludes_it_from_context(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "alpha original"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    transcript = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()
    first_assistant_id = next(message["id"] for message in transcript["messages"] if message["role"] == "assistant")
    second = client.post("/api/runs", json={"prompt": "beta abandoned", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())

    rollback = client.post(
        f"/api/conversations/{first['conversation_id']}/rollback",
        json={"target_message_id": first_assistant_id, "reason": "try a different path"},
    )
    follow_up = client.post("/api/runs", json={"prompt": "continue after rollback", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", follow_up["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    context = client.get(f"/api/runs/{follow_up['thread_id']}/context").json()
    transcript_after = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()

    assert rollback.status_code == 200
    assert any(item["kind"] == "conversation_history" and "alpha original" in item["text"] for item in fake.requests[-1].context_items)
    assert not any("beta abandoned" in item["text"] for item in fake.requests[-1].context_items)
    assert any(item["reason"] == "inactive_branch" for item in context["transcript"]["omitted"])
    assert any(message["branch_status"] == "inactive" and message["turn_id"] == second["turn_id"] for message in transcript_after["messages"])


def test_fork_inherits_source_history_until_fork_point_but_not_source_future(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "fork base"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    transcript = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()
    first_assistant_id = next(message["id"] for message in transcript["messages"] if message["role"] == "assistant")

    fork = client.post(
        f"/api/conversations/{first['conversation_id']}/fork",
        json={"source_message_id": first_assistant_id, "title": "forked branch"},
    ).json()
    source_future = client.post("/api/runs", json={"prompt": "source future only", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", source_future["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    fork_run = client.post("/api/runs", json={"prompt": "fork follow up", "conversation_id": fork["conversation"]["id"]}).json()
    with client.stream("GET", fork_run["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    fork_transcript = client.get(f"/api/conversations/{fork['conversation']['id']}/transcript").json()

    assert fork["branch_record"]["operation"] == "fork"
    assert any(item["kind"] == "conversation_history" and "fork base" in item["text"] for item in fake.requests[-1].context_items)
    assert not any("source future only" in item["text"] for item in fake.requests[-1].context_items)
    assert any(message["branch_status"] == "inherited" and message["id"] == first_assistant_id for message in fork_transcript["messages"])
    assert fork_transcript["branch_records"][0]["operation"] == "fork"


def test_branch_operations_reject_unknown_and_inactive_targets(tmp_path: Path) -> None:
    fake = FakeProvider()
    client = _client(tmp_path, provider=fake)

    first = client.post("/api/runs", json={"prompt": "base"}).json()
    with client.stream("GET", first["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    transcript = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()
    first_assistant_id = next(message["id"] for message in transcript["messages"] if message["role"] == "assistant")
    second = client.post("/api/runs", json={"prompt": "inactive later", "conversation_id": first["conversation_id"]}).json()
    with client.stream("GET", second["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    second_transcript = client.get(f"/api/conversations/{first['conversation_id']}/transcript").json()
    second_assistant_id = next(message["id"] for message in second_transcript["messages"] if message["turn_id"] == second["turn_id"] and message["role"] == "assistant")
    client.post(f"/api/conversations/{first['conversation_id']}/rollback", json={"target_message_id": first_assistant_id})

    unknown = client.post(f"/api/conversations/{first['conversation_id']}/fork", json={"source_message_id": "msg_missing"})
    inactive = client.post(f"/api/conversations/{first['conversation_id']}/fork", json={"source_message_id": second_assistant_id})

    assert unknown.status_code == 404
    assert unknown.json()["detail"]["code"] == "source_message_not_found"
    assert inactive.status_code == 409
    assert inactive.json()["detail"]["code"] == "source_inactive"


def test_resume_on_inactive_branch_is_rejected(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "kira.db"))
    client = TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=_config_store(),
            openai_provider=FakeProvider(),
            skill_registry=create_builtin_skill_registry(),
            runtime_storage=storage,
        )
    )

    base = client.post("/api/runs", json={"prompt": "active base"}).json()
    with client.stream("GET", base["events_url"]) as response:
        _read_sse_payloads(response.iter_lines())
    waiting = client.post(
        "/api/runs",
        json={"prompt": "please approve inactive branch", "skill_id": HITL_FIXTURE_SKILL_ID, "conversation_id": base["conversation_id"]},
    ).json()
    with client.stream("GET", waiting["events_url"]) as response:
        events = _read_sse_payloads(response.iter_lines())
    interrupt = next(event for event in events if event["type"] == "interrupt")
    transcript = client.get(f"/api/conversations/{base['conversation_id']}/transcript").json()
    base_assistant_id = next(message["id"] for message in transcript["messages"] if message["turn_id"] == base["turn_id"] and message["role"] == "assistant")
    client.post(f"/api/conversations/{base['conversation_id']}/rollback", json={"target_message_id": base_assistant_id})

    resumed = client.post(
        f"/api/runs/{waiting['thread_id']}/resume",
        json={"interrupt_id": interrupt["data"]["interrupt_id"], "decision": "approve"},
    )

    assert resumed.status_code == 409
    assert resumed.json()["detail"]["code"] == "inactive_branch_conflict"


def _client(tmp_path: Path, *, provider: FakeProvider | None = None) -> TestClient:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "kira.db"))
    return TestClient(create_app(fixture_delay_seconds=0, provider_config=_config_store(), openai_provider=provider or FakeProvider(), runtime_storage=storage))


def _config_store() -> ProviderConfigStore:
    return ProviderConfigStore(
        default_provider="default",
        config_path="/tmp/config.yaml",
        loaded=True,
        providers={
            "default": ProviderConfig(name="default", provider="openai", base_url="https://example.test/v1", model="model-a", api_key="sk-secret"),
        },
    )


def _read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads
