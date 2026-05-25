from fastapi.testclient import TestClient

from kira_server.main import create_app
from kira_server.providers.config import ProviderConfigStore


def make_client() -> TestClient:
    return TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
        )
    )


def test_health() -> None:
    client = make_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_run_returns_unique_thread_id_and_metadata() -> None:
    client = make_client()

    first = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"})
    second = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"})

    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["thread_id"].startswith("local-")
    assert second_body["thread_id"].startswith("local-")
    assert first_body["thread_id"] != second_body["thread_id"]
    assert first_body["status"] == "created"
    assert first_body["fixture"] == "welcome"
    assert first_body["provider"]["mode"] == "fixture"
    assert first_body["events_url"] == f"/api/runs/{first_body['thread_id']}/events"


def test_fixture_run_requires_no_network_credentials(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = make_client()

    response = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"})

    assert response.status_code == 200
    assert response.json()["thread_id"].startswith("local-")


def test_sse_streams_ordered_normalized_events() -> None:
    client = make_client()
    run = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()

    with client.stream("GET", run["events_url"]) as response:
        assert response.status_code == 200
        payloads = _read_sse_payloads(response.iter_lines())

    assert [payload["type"] for payload in payloads] == [
        "thinking_delta",
        "text_delta",
        "text_delta",
        "text_delta",
        "done",
    ]
    assert [payload["seq"] for payload in payloads] == [1, 2, 3, 4, 5]
    assert all(payload["thread_id"] == run["thread_id"] for payload in payloads)
    assert payloads[1]["data"]["kind"] == "fixture_tool_result"
    assert payloads[0]["data"]["provider"]["mode"] == "fixture"


def test_missing_provider_config_falls_back_to_fixture() -> None:
    client = make_client()

    response = client.post("/api/runs", json={"prompt": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["fixture"] == "welcome"
    assert body["provider"]["mode"] == "fixture"
    assert body["provider"]["fallback_reason"] == "missing_provider_config"


def test_unknown_run_events_return_not_found() -> None:
    client = make_client()

    response = client.get("/api/runs/missing/events")

    assert response.status_code == 404
    assert "missing" in response.json()["detail"]


def test_fixture_replay_is_deterministic_except_identifiers_and_timestamps() -> None:
    client = make_client()
    first = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    second = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()

    with client.stream("GET", first["events_url"]) as response:
        first_events = _stable_payloads(_read_sse_payloads(response.iter_lines()))
    with client.stream("GET", second["events_url"]) as response:
        second_events = _stable_payloads(_read_sse_payloads(response.iter_lines()))

    assert first_events == second_events


def test_error_fixture_streams_error_event() -> None:
    client = make_client()
    run = client.post("/api/runs", json={"prompt": "fail", "fixture": "error"}).json()

    with client.stream("GET", run["events_url"]) as response:
        payloads = _read_sse_payloads(response.iter_lines())

    assert [payload["type"] for payload in payloads] == ["thinking_delta", "error"]
    assert payloads[-1]["data"]["message"] == "Fixture error for failure-state testing"


def _read_sse_payloads(lines) -> list[dict]:
    import json

    payloads = []
    for line in lines:
        if not line.startswith("data: "):
            continue
        payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads


def _stable_payloads(payloads: list[dict]) -> list[dict]:
    stable = []
    for payload in payloads:
        data = dict(payload["data"])
        data.pop("timestamp", None)
        stable.append({"type": payload["type"], "seq": payload["seq"], "data": data})
    return stable
