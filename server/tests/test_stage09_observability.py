from fastapi.testclient import TestClient

from kira_server.main import create_app
from kira_server.providers.config import ProviderConfigStore
from kira_server.transcript import TranscriptPart


def make_client() -> TestClient:
    return TestClient(
        create_app(
            fixture_delay_seconds=0,
            provider_config=ProviderConfigStore(config_path="/missing", loaded=False),
        )
    )


def test_permission_preview_and_audit_are_redacted() -> None:
    client = make_client()

    permission = client.post(
        "/api/permissions/preview",
        json={"action": "memory.write", "subject": {"scope": "user", "api_key": "sk-secret-value"}},
    )
    assert permission.status_code == 200
    body = permission.json()
    assert body["decision"] == "ask"
    assert body["subject"]["api_key"] == "[redacted]"

    run = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    audit = client.get(f"/api/audit?thread_id={run['thread_id']}&limit=10").json()
    assert audit["redacted"] is True
    assert {record["action"] for record in audit["records"]} >= {"provider.select", "run.create"}
    assert "sk-secret-value" not in str(audit)


def test_doctor_and_run_trace_are_read_only() -> None:
    client = make_client()
    run = client.post("/api/runs", json={"prompt": "hello", "fixture": "welcome"}).json()
    with client.stream("GET", run["events_url"]) as response:
        list(response.iter_lines())

    doctor = client.get("/api/doctor")
    assert doctor.status_code == 200
    assert any(check["component"] == "audit_storage" for check in doctor.json()["checks"])

    first = client.get(f"/api/runs/{run['thread_id']}/trace").json()
    second = client.get(f"/api/runs/{run['thread_id']}/trace").json()
    assert first["scope"] == "run"
    assert len(first["events"]) == len(second["events"])
    assert first["redacted"] is True


def test_replacement_inspection_is_policy_denied_and_audited() -> None:
    client = make_client()
    service = client.app.state.transcript_service
    conversation = service.create_conversation()
    now = "2026-05-15T00:00:00+00:00"
    part = TranscriptPart(
        id="part-stage09",
        message_id="msg-stage09",
        conversation_id=conversation.id,
        turn_id="turn-stage09",
        thread_id="thread-stage09",
        kind="tool_summary",
        seq=0,
        text="summary",
        visible=False,
        created_at=now,
    )
    replacement = service._insert_tool_output_replacement(
        part,
        {"name": "fixture_tool"},
        "raw output with api_key=sk-secret-value",
        "too_large",
        "safe summary",
    )

    response = client.get(f"/api/replacements/{replacement.id}/inspect")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["metadata"]["redacted"] is True
    assert "sk-secret-value" not in str(body)

    audit = client.get(f"/api/audit?action=replacement.inspect&limit=5").json()
    assert audit["records"][0]["status"] == "denied"
