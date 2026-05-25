from __future__ import annotations

import json
from pathlib import Path

from kira_server.storage.database import RuntimeDatabase, RuntimeStorage, apply_migrations, runtime_db_path_from_env
from kira_server.storage.failure import FailureClass
from kira_server.storage.idempotency import args_hash, idempotency_key
from kira_server.storage.retry import RetryPolicy


def test_runtime_db_path_override_and_default_are_user_local(tmp_path: Path, monkeypatch) -> None:
    override = tmp_path / "runtime.db"
    monkeypatch.setenv("KIRA_RUNTIME_DB_PATH", str(override))

    assert runtime_db_path_from_env() == override

    monkeypatch.delenv("KIRA_RUNTIME_DB_PATH", raising=False)
    default = runtime_db_path_from_env()
    assert default.name == "kira.db"
    assert default.parent.name == ".kira-agent"
    assert "kira-agent/server" not in str(default)


def test_storage_initializes_and_migrations_are_idempotent(tmp_path: Path) -> None:
    database = RuntimeDatabase(tmp_path / "runtime.db")
    database.initialize()
    with database.connect() as conn:
        apply_migrations(conn)
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }

    assert {
        "run_events",
        "run_attempts",
        "provider_attempts",
        "run_locks",
        "side_effect_ledger",
        "run_projections",
        "repair_notes",
        "runtime_checkpoints",
        "project_roots",
        "project_files",
        "project_chunks",
        "memory_records",
        "memory_events",
        "memory_citations",
        "memory_tombstones",
        "memory_retrieval_traces",
        "memory_candidates",
        "memory_candidate_decisions",
    }.issubset(tables)


def test_event_sequence_projection_and_replay_are_stable(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    storage.create_projection(
        thread_id="local-1",
        status="created",
        prompt="hello",
        provider_metadata={"mode": "fixture", "fixture": "welcome"},
        fixture="welcome",
    )

    first = storage.append_event(thread_id="local-1", event_type="text_delta", data={"text": "one"})
    second = storage.append_event(thread_id="local-1", event_type="done", data={"message": "done"})
    replayed = storage.list_events("local-1", after_seq=1)
    state = storage.state_projection("local-1")

    assert first.seq == 1
    assert second.seq == 2
    assert [event.seq for event in replayed] == [2]
    assert state is not None
    assert state["latest_seq"] == 2


def test_run_locks_conflict_release_and_stale_takeover(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))

    acquired, first = storage.acquire_lock("local-lock", owner="a", ttl_seconds=100)
    duplicate, active = storage.acquire_lock("local-lock", owner="b", ttl_seconds=100)
    storage.release_lock("local-lock")
    reacquired, released = storage.acquire_lock("local-lock", owner="c", ttl_seconds=100)
    storage.release_lock("local-lock")
    storage.acquire_lock("local-lock", owner="old", ttl_seconds=-1)
    takeover, stale = storage.acquire_lock("local-lock", owner="new", ttl_seconds=100)

    assert acquired is True
    assert first["owner"] == "a"
    assert duplicate is False
    assert active["owner"] == "a"
    assert reacquired is True
    assert released["owner"] == "c"
    assert takeover is True
    assert stale["takeover_count"] >= 1


def test_provider_attempt_and_repair_notes_are_redacted(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    storage.create_projection(
        thread_id="local-1",
        status="created",
        prompt="hello",
        provider_metadata={"mode": "real", "name": "default", "model": "m", "api_key": "sk-...cret"},
    )

    storage.record_provider_attempt(
        thread_id="local-1",
        provider_metadata={"mode": "real", "name": "default", "model": "m", "api_key": "sk-...cret"},
        status="error",
        retry_count=2,
        timeout=3,
        error_summary="failed with sk-secret",
    )
    storage.add_repair_note(thread_id="local-1", note="checked config", source="test")
    exported = storage.debug_export("local-1")

    assert exported is not None
    dumped = json.dumps(exported)
    assert "sk-secret" not in dumped
    assert "sk-...cret" in dumped
    assert exported["state"]["provider_attempts"][0]["retry_count"] == 2
    assert exported["state"]["repair_notes"][0]["note"] == "checked config"


def test_idempotency_key_and_ledger_reuse(tmp_path: Path) -> None:
    storage = RuntimeStorage(RuntimeDatabase(tmp_path / "runtime.db"))
    arguments = {"path": "README.md", "limit": 1}
    first = idempotency_key(
        thread_id="local-1",
        checkpoint_id="latest",
        node_name="tool_step",
        call_index=0,
        tool_name="read_project_file",
        arguments=arguments,
    )
    second = idempotency_key(
        thread_id="local-1",
        checkpoint_id="latest",
        node_name="tool_step",
        call_index=0,
        tool_name="read_project_file",
        arguments=arguments,
    )
    changed = idempotency_key(
        thread_id="local-1",
        checkpoint_id="latest",
        node_name="tool_step",
        call_index=0,
        tool_name="read_project_file",
        arguments={**arguments, "limit": 2},
    )
    storage.ledger_record(
        key=first,
        thread_id="local-1",
        checkpoint_id="latest",
        node="tool_step",
        tool="read_project_file",
        args_hash_value=args_hash(arguments),
        status="completed",
        result_summary={"ok": True},
    )

    assert first == second
    assert first != changed
    assert storage.ledger_get(first)["status"] == "completed"
    assert storage.ledger_get(first)["result_summary"] == {"ok": True}


def test_retry_policy_respects_class_attempts_and_idempotency() -> None:
    policy = RetryPolicy(max_attempts=2)

    retry = policy.decide(failure_class=FailureClass.TIMEOUT, attempt_number=1, idempotent=True)
    no_attempts = policy.decide(failure_class=FailureClass.TIMEOUT, attempt_number=2, idempotent=True)
    validation = policy.decide(failure_class=FailureClass.VALIDATION, attempt_number=1, idempotent=True)
    unsafe = policy.decide(failure_class=FailureClass.TIMEOUT, attempt_number=1, idempotent=False)

    assert retry.retry is True
    assert no_attempts.retry is False
    assert no_attempts.reason == "retry_exhausted"
    assert validation.retry is False
    assert unsafe.reason == "not_idempotent"
