from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

from kira_server.core.events import ProviderEvent
from kira_server.main import create_app
from kira_server.memory import MemoryCreateRequest, MemorySearchRequest, MemoryService
from kira_server.providers.base import ProviderRequest
from kira_server.providers.config import ProviderConfig, ProviderConfigStore
from kira_server.storage.database import RuntimeDatabase, RuntimeStorage


class FakeProvider:
    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        yield ProviderEvent(type="text_delta", data={"text": "remote"})
        yield ProviderEvent(type="done", data={"message": "done"})


def config_store() -> ProviderConfigStore:
    return ProviderConfigStore(
        default_provider="default",
        config_path="/tmp/config.yaml",
        loaded=True,
        providers={
            "default": ProviderConfig(name="default", provider="openai", base_url="https://example.test/v1", model="model-a", api_key="sk-secret"),
        },
    )


def test_memory_crud_filters_lifecycle_and_tombstone(tmp_path: Path) -> None:
    client = _client(tmp_path)

    created = client.post(
        "/api/memory",
        json={
            "scope": "projectLocal",
            "type": "preference",
            "text": "User prefers concise summaries",
            "tags": ["style", "summary"],
            "confidence": 0.9,
            "source": {"kind": "manual", "summary": "user said so"},
        },
    ).json()["memory"]
    listed = client.get("/api/memory?scope=projectLocal&type=preference&tag=style").json()
    stale = client.put(f"/api/memory/{created['id']}", json={"status": "stale"}).json()["memory"]
    archived = client.post(f"/api/memory/{created['id']}/actions", json={"action": "archive"}).json()["memory"]
    deleted = client.delete(f"/api/memory/{created['id']}").json()

    assert listed["memories"][0]["id"] == created["id"]
    assert stale["status"] == "stale"
    assert archived["status"] == "archived"
    assert deleted == {"deleted": True, "memory_id": created["id"]}
    assert client.get(f"/api/memory/{created['id']}").status_code == 404


def test_memory_secret_guard_rejects_and_does_not_persist_raw_secret(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    client = _client(tmp_path, storage=storage)

    response = client.post(
        "/api/memory",
        json={"scope": "user", "type": "fact", "text": "api_key = sk-secret-value-123456789"},
    )

    assert response.status_code == 400
    with storage.database.connect() as conn:
        rows = [json.dumps(dict(row), default=str) for row in conn.execute("SELECT * FROM memory_records").fetchall()]
        events = [json.dumps(dict(row), default=str) for row in conn.execute("SELECT * FROM memory_events").fetchall()]
    assert "sk-secret-value" not in "\n".join(rows + events)


def test_memory_retrieval_context_injection_and_replay_are_redacted(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    fake = FakeProvider()
    client = _client(tmp_path, storage=storage, provider=fake)
    first = client.post("/api/memory", json={"scope": "projectLocal", "type": "decision", "text": "Use SQLite for durable local memory", "tags": ["sqlite"], "confidence": 0.95}).json()["memory"]
    client.post("/api/memory", json={"scope": "projectLocal", "type": "decision", "text": "Use SQLite for durable local memory", "tags": ["duplicate"], "confidence": 0.7})
    client.post("/api/memory", json={"scope": "projectLocal", "type": "fact", "text": "Archived memory should not inject", "status": "archived"})

    search = client.post("/api/memory/search", json={"query": "SQLite memory", "top_k": 5}).json()
    run = client.post("/api/runs", json={"prompt": "remember memory choice", "include_memory": True, "memory_query": "SQLite memory"}).json()
    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())
    trace = client.get(f"/api/runs/{run['thread_id']}/context").json()
    state = client.get(f"/api/runs/{run['thread_id']}/state").json()
    replay_before = client.get(f"/api/runs/{run['thread_id']}/replay").json()
    replay_after = client.get(f"/api/runs/{run['thread_id']}/replay").json()

    assert search["results"][0]["memory"]["id"] == first["id"]
    assert search["results"][0]["score_reasons"]
    assert search["results"][0]["duplicate_ids"]
    assert run["context"]["memory_count"] == 1
    assert fake.requests[0].context_items
    assert any(item["kind"] == "memory" for item in trace["included"])
    assert trace["memory"]["citations"][0]["memory_id"] == first["id"]
    assert state["memory_citations"][0]["memory_id"] == first["id"]
    assert replay_before == replay_after
    assert "sk-secret" not in json.dumps(trace)
    assert payloads[-1]["type"] == "done"


def test_extraction_dry_run_candidate_decisions_and_lifecycle_approval(tmp_path: Path) -> None:
    client = _client(tmp_path)

    dry_run = client.post("/api/memory/extract", json={"prompt": "User prefers concise answers", "dry_run": True}).json()
    candidate = dry_run["candidates"][0]
    approved = client.post(f"/api/memory/candidates/{candidate['id']}/decisions", json={"decision": "approve"}).json()
    promote = client.post(f"/api/memory/{approved['memory']['id']}/actions", json={"action": "promote", "target_scope": "user"}).json()
    promoted = client.post(f"/api/memory/{approved['memory']['id']}/actions", json={"action": "promote", "target_scope": "user", "approved": True}).json()
    blocked = client.post("/api/memory/extract", json={"prompt": "Remember Bearer secret-token-value-123456789", "dry_run": True}).json()["candidates"][0]

    assert dry_run["status"] == "dry_run"
    assert approved["memory"]["text"] == candidate["text"]
    assert promote["approval_required"] is True
    assert promoted["memory"]["scope"] == "user"
    assert blocked["status"] == "blocked"
    assert "secret-token-value" not in json.dumps(blocked)


def test_memory_service_status_scope_and_expiry_filters(tmp_path: Path) -> None:
    service = MemoryService(_storage(tmp_path))
    active = service.create(MemoryCreateRequest(scope="session", type="fact", text="session active memory", thread_id="thread-a"))
    service.create(MemoryCreateRequest(scope="session", type="fact", text="other session memory", thread_id="thread-b"))
    service.create(MemoryCreateRequest(scope="projectLocal", type="fact", text="expired memory", expires_at="2000-01-01T00:00:00+00:00"))

    response = service.search(MemorySearchRequest(query="memory", thread_id="thread-a", scopes=["session"], top_k=10), thread_id="thread-a", inject=True)

    assert [result.memory.id for result in response.results] == [active.id]


def _storage(tmp_path: Path) -> RuntimeStorage:
    return RuntimeStorage(RuntimeDatabase(tmp_path / "kira.db"))


def _client(tmp_path: Path, *, storage: RuntimeStorage | None = None, provider: FakeProvider | None = None) -> TestClient:
    return TestClient(create_app(fixture_delay_seconds=0, provider_config=config_store(), openai_provider=provider or FakeProvider(), runtime_storage=storage or _storage(tmp_path)))


def _read_sse_payloads(lines) -> list[dict]:
    payloads = []
    for line in lines:
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads
