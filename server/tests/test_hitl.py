from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kira_server.graph_runtime.hitl import ResumeRequest, make_interrupt, validate_resume_for_interrupt
from kira_server.graph_runtime.streaming import map_langgraph_event
from kira_server.main import create_app
from kira_server.providers.config import ProviderConfigStore
from kira_server.skills.builtin import HITL_FIXTURE_SKILL_ID, create_builtin_skill_registry
from kira_server.storage.database import RuntimeDatabase, RuntimeStorage


def test_interrupt_payload_validation_redacts_secrets() -> None:
    interrupt = make_interrupt(
        kind="approval",
        title="Approve sk-secret",
        body="Body sk-secret",
        data={"api_key": "sk-secret", "visible": "ok"},
    )

    dumped = json.dumps(interrupt.public_dict())
    assert "sk-secret" not in dumped
    assert "api_key" not in dumped
    assert interrupt.allowed_responses[0].kind == "approve"


def test_resume_validation_rejects_stale_interrupt() -> None:
    pending = make_interrupt(kind="approval", title="Approve", body="Continue?").public_dict()

    with pytest.raises(ValueError):
        validate_resume_for_interrupt(pending, ResumeRequest(interrupt_id="other", decision="approve"))


def test_langgraph_event_mapper_tolerates_unknown_events() -> None:
    assert map_langgraph_event({"event": "unknown_event", "data": {"secret": "sk-secret"}}) is None
    mapped = map_langgraph_event({"event": "on_tool_start", "name": "list_project_files", "data": {}})
    assert mapped is not None
    assert mapped.type == "tool_start"


def test_hitl_approval_resume_same_thread_and_replay(tmp_path: Path) -> None:
    client = hitl_client(tmp_path)

    run = client.post(
        "/api/runs",
        json={"prompt": "please approve", "skill_id": HITL_FIXTURE_SKILL_ID},
    ).json()
    with client.stream("GET", run["events_url"]) as response:
        initial = read_sse_payloads(response.iter_lines())
    state = client.get(f"/api/runs/{run['thread_id']}/state").json()

    interrupt = next(event for event in initial if event["type"] == "interrupt")
    with client.stream("GET", f"{run['events_url']}?after_seq=0") as response:
        replay_waiting = read_sse_payloads(response.iter_lines())
    resumed = client.post(
        f"/api/runs/{run['thread_id']}/resume",
        json={"interrupt_id": interrupt["data"]["interrupt_id"], "decision": "approve"},
    )
    final_state = client.get(f"/api/runs/{run['thread_id']}/state").json()
    replay = client.get(f"/api/runs/{run['thread_id']}/replay").json()

    assert run["resume_url"] == f"/api/runs/{run['thread_id']}/resume"
    assert state["status"] == "waiting_for_user"
    assert state["pending_interrupt"]["interrupt_id"] == interrupt["data"]["interrupt_id"]
    assert [event["seq"] for event in replay_waiting] == [event["seq"] for event in initial]
    assert resumed.status_code == 200
    assert resumed.json()["thread_id"] == run["thread_id"]
    assert [event["type"] for event in resumed.json()["events"]] == ["resume", "text_delta", "done"]
    assert final_state["status"] == "completed"
    assert final_state["pending_interrupt"] is None
    assert [event["type"] for event in replay["events"]].count("interrupt") == 1
    assert [event["type"] for event in replay["events"]].count("resume") == 1


def test_hitl_reject_edit_question_and_python_paths(tmp_path: Path) -> None:
    client = hitl_client(tmp_path)

    approval = start_waiting(client, "please approve")
    rejected = client.post(
        f"/api/runs/{approval['thread_id']}/resume",
        json={"interrupt_id": approval["interrupt_id"], "decision": "reject", "reason": "not now"},
    ).json()
    edit = start_waiting(client, "please edit")
    edited = client.post(
        f"/api/runs/{edit['thread_id']}/resume",
        json={"interrupt_id": edit["interrupt_id"], "decision": "submit", "value": "edited text"},
    ).json()
    question = start_waiting(client, "please ask a question")
    answered = client.post(
        f"/api/runs/{question['thread_id']}/resume",
        json={"interrupt_id": question["interrupt_id"], "decision": "submit", "value": "answer"},
    ).json()
    python = start_waiting(client, "please run python")
    approved = client.post(
        f"/api/runs/{python['thread_id']}/resume",
        json={"interrupt_id": python["interrupt_id"], "decision": "approve"},
    ).json()

    assert rejected["events"][1]["type"] == "tool_result"
    assert "Edited value accepted" in rejected_or_text(edited)
    assert "Answer received" in rejected_or_text(answered)
    assert approved["events"][1]["type"] == "tool_result"


def test_hitl_resume_errors_are_structured(tmp_path: Path) -> None:
    client = hitl_client(tmp_path)
    waiting = start_waiting(client, "please approve")

    stale = client.post(
        f"/api/runs/{waiting['thread_id']}/resume",
        json={"interrupt_id": "stale", "decision": "approve"},
    )
    missing = client.post("/api/runs/missing/resume", json={"interrupt_id": "x", "decision": "approve"})

    assert stale.status_code == 400
    assert stale.json()["detail"]["code"] == "invalid_resume"
    assert missing.status_code == 404


def hitl_client(tmp_path: Path) -> TestClient:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    return TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
            skill_registry=create_builtin_skill_registry(),
            runtime_storage=storage,
        )
    )


def start_waiting(client: TestClient, prompt: str) -> dict:
    run = client.post("/api/runs", json={"prompt": prompt, "skill_id": HITL_FIXTURE_SKILL_ID}).json()
    with client.stream("GET", run["events_url"]) as response:
        events = read_sse_payloads(response.iter_lines())
    interrupt = next(event for event in events if event["type"] == "interrupt")
    return {"thread_id": run["thread_id"], "interrupt_id": interrupt["data"]["interrupt_id"]}


def read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads


def rejected_or_text(payload: dict) -> str:
    return json.dumps(payload["events"], ensure_ascii=False)
