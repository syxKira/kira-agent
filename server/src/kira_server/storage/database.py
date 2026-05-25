from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from kira_server.core.events import KiraEvent
from kira_server.providers.config import redact_text
from kira_server.safety import redact_value
from kira_server.storage.failure import FailureClass, classify_error_code

RUNTIME_DB_PATH_ENV = "KIRA_RUNTIME_DB_PATH"
DEFAULT_RUNTIME_DB_PATH = Path.home() / ".kira-agent" / "kira.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_db_path_from_env() -> Path:
    override = os.environ.get(RUNTIME_DB_PATH_ENV)
    return Path(override).expanduser() if override else DEFAULT_RUNTIME_DB_PATH


@dataclass(frozen=True)
class RuntimeDatabase:
    path: Path

    @classmethod
    def from_env(cls) -> "RuntimeDatabase":
        return cls(runtime_db_path_from_env())

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            apply_migrations(conn)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class RuntimeStorage:
    def __init__(self, database: RuntimeDatabase) -> None:
        self.database = database
        self.audit_diagnostics: list[dict[str, Any]] = []
        self.database.initialize()

    @classmethod
    def from_env(cls) -> "RuntimeStorage":
        return cls(RuntimeDatabase.from_env())

    def create_projection(
        self,
        *,
        thread_id: str,
        status: str,
        prompt: str,
        provider_metadata: dict[str, Any],
        fixture: str | None = None,
        skill_metadata: dict[str, Any] | None = None,
        workflow_name: str | None = None,
        project_root: str | None = None,
        model: str | None = None,
        conversation_id: str | None = None,
        turn_id: str | None = None,
        user_message_id: str | None = None,
        assistant_message_id: str | None = None,
        transcript_status: str | None = None,
        active_head_message_id: str | None = None,
        branch_metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO run_projections (
                  thread_id, status, prompt, provider_metadata_json, fixture, skill_metadata_json,
                  workflow_name, project_root, model, fixture_fallback, latest_seq,
                  repair_required, pending_interrupt_json, conversation_id, turn_id,
                  user_message_id, assistant_message_id, transcript_status, active_head_message_id,
                  branch_metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                  status=excluded.status,
                  prompt=excluded.prompt,
                  provider_metadata_json=excluded.provider_metadata_json,
                  fixture=excluded.fixture,
                  skill_metadata_json=excluded.skill_metadata_json,
                  workflow_name=excluded.workflow_name,
                  project_root=excluded.project_root,
                  model=excluded.model,
                  fixture_fallback=excluded.fixture_fallback,
                  conversation_id=excluded.conversation_id,
                  turn_id=excluded.turn_id,
                  user_message_id=excluded.user_message_id,
                  assistant_message_id=excluded.assistant_message_id,
                  transcript_status=excluded.transcript_status,
                  active_head_message_id=excluded.active_head_message_id,
                  branch_metadata_json=excluded.branch_metadata_json,
                  updated_at=excluded.updated_at
                """,
                (
                    thread_id,
                    status,
                    prompt,
                    _json(provider_metadata),
                    fixture,
                    _json(skill_metadata),
                    workflow_name,
                    project_root,
                    model,
                    1 if provider_metadata.get("mode") == "fixture" else 0,
                    conversation_id,
                    turn_id,
                    user_message_id,
                    assistant_message_id,
                    transcript_status,
                    active_head_message_id,
                    _json(branch_metadata),
                    utc_now(),
                    utc_now(),
                ),
            )

    def update_projection(
        self,
        thread_id: str,
        *,
        status: str | None = None,
        failure_class: str | None = None,
        repair_required: bool | None = None,
        pending_interrupt: dict[str, Any] | None = None,
    ) -> None:
        with self.database.connect() as conn:
            current = conn.execute("SELECT * FROM run_projections WHERE thread_id = ?", (thread_id,)).fetchone()
            if current is None:
                return
            conn.execute(
                """
                UPDATE run_projections
                SET status = ?, failure_class = ?, repair_required = ?, pending_interrupt_json = ?, updated_at = ?
                WHERE thread_id = ?
                """,
                (
                    status if status is not None else current["status"],
                    failure_class if failure_class is not None else current["failure_class"],
                    int(repair_required) if repair_required is not None else current["repair_required"],
                    _json(pending_interrupt) if pending_interrupt is not None else current["pending_interrupt_json"],
                    utc_now(),
                    thread_id,
                ),
            )

    def clear_pending_interrupt(self, thread_id: str, *, status: str | None = None) -> None:
        with self.database.connect() as conn:
            current = conn.execute("SELECT * FROM run_projections WHERE thread_id = ?", (thread_id,)).fetchone()
            if current is None:
                return
            conn.execute(
                """
                UPDATE run_projections
                SET status = ?, pending_interrupt_json = NULL, updated_at = ?
                WHERE thread_id = ?
                """,
                (status if status is not None else current["status"], utc_now(), thread_id),
            )

    def append_event(self, *, thread_id: str, event_type: str, data: dict[str, Any]) -> KiraEvent:
        now = utc_now()
        event_data = {**data, "timestamp": data.get("timestamp") or now}
        with self.database.connect() as conn:
            row = conn.execute("SELECT COALESCE(MAX(seq), 0) AS last_seq FROM run_events WHERE thread_id = ?", (thread_id,)).fetchone()
            seq = int(row["last_seq"]) + 1
            conn.execute(
                "INSERT INTO run_events(thread_id, seq, type, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (thread_id, seq, event_type, _json(event_data), now),
            )
            conn.execute(
                "UPDATE run_projections SET latest_seq = ?, updated_at = ? WHERE thread_id = ?",
                (seq, now, thread_id),
            )
        return KiraEvent(type=event_type, thread_id=thread_id, seq=seq, data=event_data)

    def list_events(self, thread_id: str, *, after_seq: int = 0) -> list[KiraEvent]:
        with self.database.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM run_events WHERE thread_id = ? AND seq > ? ORDER BY seq",
                (thread_id, after_seq),
            ).fetchall()
        return [
            KiraEvent(type=row["type"], thread_id=row["thread_id"], seq=row["seq"], data=_loads(row["data_json"]) or {})
            for row in rows
        ]

    def create_attempt(self, *, thread_id: str, skill_id: str | None, model: str | None, durability_mode: str) -> int:
        with self.database.connect() as conn:
            row = conn.execute("SELECT COALESCE(MAX(attempt_number), 0) AS last_attempt FROM run_attempts WHERE thread_id = ?", (thread_id,)).fetchone()
            attempt_number = int(row["last_attempt"]) + 1
            cursor = conn.execute(
                """
                INSERT INTO run_attempts(thread_id, attempt_number, status, durability_mode, skill_id, model, started_at)
                VALUES (?, ?, 'running', ?, ?, ?, ?)
                """,
                (thread_id, attempt_number, durability_mode, skill_id, model, utc_now()),
            )
            return int(cursor.lastrowid)

    def finish_attempt(self, attempt_id: int, *, status: str, failure_class: str | None = None) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE run_attempts SET status = ?, failure_class = ?, ended_at = ? WHERE id = ?",
                (status, failure_class, utc_now(), attempt_id),
            )

    def record_provider_attempt(
        self,
        *,
        thread_id: str,
        provider_metadata: dict[str, Any],
        status: str,
        retry_count: int = 0,
        timeout: float | None = None,
        error_summary: str | None = None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO provider_attempts(
                  thread_id, provider_profile, model, timeout, retry_count, fallback, fallback_reason,
                  status, error_summary, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    provider_metadata.get("name") or provider_metadata.get("provider") or provider_metadata.get("fixture"),
                    provider_metadata.get("model"),
                    timeout,
                    retry_count,
                    1 if provider_metadata.get("mode") == "fixture" else 0,
                    provider_metadata.get("fallback_reason"),
                    status,
                    redact_text(error_summary),
                    _json(provider_metadata),
                    utc_now(),
                ),
            )

    def acquire_lock(self, thread_id: str, *, owner: str | None = None, ttl_seconds: int = 30) -> tuple[bool, dict[str, Any]]:
        owner_id = owner or f"owner-{uuid4().hex}"
        now = utc_now()
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        with self.database.connect() as conn:
            row = conn.execute("SELECT * FROM run_locks WHERE thread_id = ?", (thread_id,)).fetchone()
            if row and row["status"] == "active" and row["expires_at"] > now:
                return False, _row_dict(row)
            takeover_count = int(row["takeover_count"]) + 1 if row else 0
            conn.execute(
                """
                INSERT INTO run_locks(thread_id, owner, status, heartbeat_at, expires_at, takeover_count, takeover_metadata_json, updated_at)
                VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                  owner=excluded.owner,
                  status='active',
                  heartbeat_at=excluded.heartbeat_at,
                  expires_at=excluded.expires_at,
                  takeover_count=excluded.takeover_count,
                  takeover_metadata_json=excluded.takeover_metadata_json,
                  updated_at=excluded.updated_at
                """,
                (
                    thread_id,
                    owner_id,
                    now,
                    expires_at,
                    takeover_count,
                    _json({"taken_over_at": now, "previous_owner": row["owner"]} if row else None),
                    now,
                ),
            )
        return True, {"thread_id": thread_id, "owner": owner_id, "status": "active", "expires_at": expires_at, "takeover_count": takeover_count}

    def heartbeat_lock(self, thread_id: str, *, ttl_seconds: int = 30) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE run_locks SET heartbeat_at = ?, expires_at = ?, updated_at = ? WHERE thread_id = ?",
                (
                    utc_now(),
                    (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(),
                    utc_now(),
                    thread_id,
                ),
            )

    def release_lock(self, thread_id: str, *, status: str = "released") -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE run_locks SET status = ?, updated_at = ? WHERE thread_id = ?",
                (status, utc_now(), thread_id),
            )

    def get_lock(self, thread_id: str) -> dict[str, Any] | None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT * FROM run_locks WHERE thread_id = ?", (thread_id,)).fetchone()
        return _row_dict(row) if row else None

    def save_checkpoint(self, *, thread_id: str, checkpoint_id: str, state: dict[str, Any]) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_checkpoints(thread_id, checkpoint_id, state_json, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(thread_id, checkpoint_id) DO UPDATE SET state_json=excluded.state_json, created_at=excluded.created_at
                """,
                (thread_id, checkpoint_id, _json(state), utc_now()),
            )

    def get_checkpoint(self, thread_id: str, checkpoint_id: str = "latest") -> dict[str, Any] | None:
        with self.database.connect() as conn:
            row = conn.execute(
                "SELECT state_json FROM runtime_checkpoints WHERE thread_id = ? AND checkpoint_id = ?",
                (thread_id, checkpoint_id),
            ).fetchone()
        return _loads(row["state_json"]) if row else None

    def ledger_get(self, key: str) -> dict[str, Any] | None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT * FROM side_effect_ledger WHERE idempotency_key = ?", (key,)).fetchone()
        return _ledger_row(row) if row else None

    def ledger_record(
        self,
        *,
        key: str,
        thread_id: str,
        checkpoint_id: str,
        node: str,
        tool: str,
        args_hash_value: str,
        status: str,
        result_summary: dict[str, Any] | None = None,
    ) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO side_effect_ledger(
                  idempotency_key, thread_id, checkpoint_id, node, tool, args_hash, status,
                  result_summary_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                  status=excluded.status,
                  result_summary_json=excluded.result_summary_json,
                  updated_at=excluded.updated_at
                """,
                (key, thread_id, checkpoint_id, node, tool, args_hash_value, status, _json(result_summary), utc_now(), utc_now()),
            )

    def add_repair_note(self, *, thread_id: str, note: str, source: str = "developer") -> dict[str, Any]:
        with self.database.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO repair_notes(thread_id, source, note, created_at) VALUES (?, ?, ?, ?)",
                (thread_id, source, note, utc_now()),
            )
            note_id = int(cursor.lastrowid)
        return {"id": note_id, "thread_id": thread_id, "source": source, "note": note, "created_at": utc_now()}

    def record_audit(
        self,
        *,
        action: str,
        status: str,
        decision: str | None = None,
        thread_id: str | None = None,
        conversation_id: str | None = None,
        turn_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        tool: str | None = None,
        skill_id: str | None = None,
        memory_id: str | None = None,
        project_root: str | None = None,
        metadata: dict[str, Any] | None = None,
        summary: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        audit_id = f"audit_{uuid4().hex}"
        safe_metadata = redact_value(metadata or {})
        safe_summary = redact_text(summary)
        try:
            with self.database.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_records(
                      id, action, status, decision, thread_id, conversation_id, turn_id,
                      provider, model, tool, skill_id, memory_id, project_root,
                      metadata_json, summary, redacted, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        audit_id,
                        action,
                        status,
                        decision,
                        thread_id,
                        conversation_id,
                        turn_id,
                        provider,
                        model,
                        tool,
                        skill_id,
                        memory_id,
                        project_root,
                        _json(safe_metadata),
                        safe_summary,
                        now,
                    ),
                )
        except Exception as exc:
            self.audit_diagnostics.append(
                {
                    "component": "audit_storage",
                    "status": "warning",
                    "severity": "warning",
                    "message": "Audit record could not be written",
                    "evidence": {"action": action, "error_type": type(exc).__name__, "error": redact_text(str(exc))},
                    "created_at": now,
                }
            )
        return {
            "id": audit_id,
            "action": action,
            "status": status,
            "decision": decision,
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "provider": provider,
            "model": model,
            "tool": tool,
            "skill_id": skill_id,
            "memory_id": memory_id,
            "project_root": project_root,
            "metadata": safe_metadata,
            "summary": safe_summary,
            "redacted": True,
            "created_at": now,
        }

    def list_audit_records(
        self,
        *,
        thread_id: str | None = None,
        conversation_id: str | None = None,
        project_root: str | None = None,
        memory_id: str | None = None,
        action: str | None = None,
        status: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("thread_id", thread_id),
            ("conversation_id", conversation_id),
            ("project_root", project_root),
            ("memory_id", memory_id),
            ("action", action),
            ("status", status),
        ):
            if value:
                clauses.append(f"{column} = ?")
                params.append(value)
        if since:
            clauses.append("created_at >= ?")
            params.append(since)
        if until:
            clauses.append("created_at <= ?")
            params.append(until)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, min(limit, 500)))
        with self.database.connect() as conn:
            rows = conn.execute(f"SELECT * FROM audit_records {where} ORDER BY created_at DESC LIMIT ?", params).fetchall()
        records = [_row_dict(row) for row in rows]
        for record in records:
            if record is not None and "redacted" in record:
                record["redacted"] = bool(record["redacted"])
        return records

    def state_projection(self, thread_id: str) -> dict[str, Any] | None:
        with self.database.connect() as conn:
            projection = conn.execute("SELECT * FROM run_projections WHERE thread_id = ?", (thread_id,)).fetchone()
            if projection is None:
                return None
            attempts = [_row_dict(row) for row in conn.execute("SELECT * FROM run_attempts WHERE thread_id = ? ORDER BY attempt_number", (thread_id,)).fetchall()]
            provider_attempts = [_row_dict(row) for row in conn.execute("SELECT * FROM provider_attempts WHERE thread_id = ? ORDER BY id", (thread_id,)).fetchall()]
            ledger = [_ledger_row(row) for row in conn.execute("SELECT * FROM side_effect_ledger WHERE thread_id = ? ORDER BY created_at", (thread_id,)).fetchall()]
            notes = [_row_dict(row) for row in conn.execute("SELECT * FROM repair_notes WHERE thread_id = ? ORDER BY created_at", (thread_id,)).fetchall()]
            lock = conn.execute("SELECT * FROM run_locks WHERE thread_id = ?", (thread_id,)).fetchone()
            checkpoints = [_row_dict(row) for row in conn.execute("SELECT thread_id, checkpoint_id, created_at FROM runtime_checkpoints WHERE thread_id = ? ORDER BY created_at", (thread_id,)).fetchall()]
            memory_citations = [_row_dict(row) for row in conn.execute("SELECT * FROM memory_citations WHERE thread_id = ? ORDER BY created_at", (thread_id,)).fetchall()]
            memory_candidates = [_row_dict(row) for row in conn.execute("SELECT id, status, suggested_scope, suggested_type, confidence, risk, source_json, created_at, updated_at FROM memory_candidates WHERE thread_id = ? ORDER BY created_at", (thread_id,)).fetchall()]
            transcript_parts = [_row_dict(row) for row in conn.execute("SELECT id, message_id, kind, text, visible, created_at FROM transcript_parts WHERE thread_id = ? ORDER BY created_at, seq", (thread_id,)).fetchall()]
            conversation_id = projection["conversation_id"] if "conversation_id" in projection.keys() else None
            compaction_rows = (
                conn.execute("SELECT * FROM conversation_compaction_summaries WHERE conversation_id = ? ORDER BY created_at", (conversation_id,)).fetchall()
                if conversation_id
                else []
            )
            replacement_rows = conn.execute(
                "SELECT * FROM tool_output_replacements WHERE thread_id = ? ORDER BY created_at",
                (thread_id,),
            ).fetchall()
            context_trace = conn.execute("SELECT trace_json FROM run_context_traces WHERE thread_id = ?", (thread_id,)).fetchone()
        compaction_summaries = [_row_dict(row) for row in compaction_rows]
        for summary in compaction_summaries:
            if summary is not None:
                summary["stale"] = summary.get("status") == "stale"
        tool_output_replacements = [_row_dict(row) for row in replacement_rows]
        return {
            "thread_id": thread_id,
            "status": projection["status"],
            "prompt": projection["prompt"],
            "fixture": projection["fixture"],
            "skill": _loads(projection["skill_metadata_json"]),
            "workflow": {"name": projection["workflow_name"]} if projection["workflow_name"] else None,
            "provider": _loads(projection["provider_metadata_json"]) or {},
            "model": projection["model"],
            "fixture_fallback": bool(projection["fixture_fallback"]),
            "latest_seq": projection["latest_seq"],
            "failure_class": projection["failure_class"],
            "repair_required": bool(projection["repair_required"]),
            "pending_interrupt": _loads(projection["pending_interrupt_json"]),
            "attempts": attempts,
            "provider_attempts": provider_attempts,
            "side_effects": ledger,
            "repair_notes": notes,
            "lock": _row_dict(lock) if lock else None,
            "checkpoints": checkpoints,
            "memory_citations": memory_citations,
            "memory_candidates": memory_candidates,
            "conversation_id": conversation_id,
            "turn_id": projection["turn_id"] if "turn_id" in projection.keys() else None,
            "user_message_id": projection["user_message_id"] if "user_message_id" in projection.keys() else None,
            "assistant_message_id": projection["assistant_message_id"] if "assistant_message_id" in projection.keys() else None,
            "transcript_status": projection["transcript_status"] if "transcript_status" in projection.keys() else None,
            "active_head_message_id": projection["active_head_message_id"] if "active_head_message_id" in projection.keys() else None,
            "branch_metadata": _loads(projection["branch_metadata_json"]) if "branch_metadata_json" in projection.keys() else None,
            "transcript_parts": transcript_parts,
            "compaction_summaries": compaction_summaries,
            "tool_output_replacements": tool_output_replacements,
            "context_trace": _loads(context_trace["trace_json"]) if context_trace else None,
            "audit_ids": [record["id"] for record in self.list_audit_records(thread_id=thread_id, limit=100)],
            "permission_decisions": [],
            "doctor_status": None,
            "trace_export_refs": [],
        }

    def debug_export(self, thread_id: str) -> dict[str, Any] | None:
        state = self.state_projection(thread_id)
        if state is None:
            return None
        return {
            "thread_id": thread_id,
            "state": state,
            "events": [event.model_dump() for event in self.list_events(thread_id)],
            "audit": self.list_audit_records(thread_id=thread_id, limit=100),
            "redacted": True,
        }

    def save_context_trace(self, thread_id: str, trace: dict[str, Any]) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO run_context_traces(thread_id, trace_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET trace_json=excluded.trace_json, updated_at=excluded.updated_at
                """,
                (thread_id, _json(trace), utc_now(), utc_now()),
            )

    def get_context_trace(self, thread_id: str) -> dict[str, Any] | None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT trace_json FROM run_context_traces WHERE thread_id = ?", (thread_id,)).fetchone()
        return _loads(row["trace_json"]) if row else None

    def mark_active_cancelled_for_shutdown(self) -> None:
        with self.database.connect() as conn:
            conn.execute("UPDATE run_locks SET status = 'shutdown', updated_at = ? WHERE status = 'active'", (utc_now(),))
            conn.execute(
                "UPDATE run_projections SET status = 'cancelled', failure_class = ?, updated_at = ? WHERE status IN ('created', 'running', 'cancelling')",
                (FailureClass.CANCELLED.value, utc_now()),
            )


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version INTEGER PRIMARY KEY,
          applied_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_events (
          thread_id TEXT NOT NULL,
          seq INTEGER NOT NULL,
          type TEXT NOT NULL,
          data_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(thread_id, seq)
        );
        CREATE TABLE IF NOT EXISTS run_attempts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          thread_id TEXT NOT NULL,
          attempt_number INTEGER NOT NULL,
          status TEXT NOT NULL,
          durability_mode TEXT NOT NULL,
          skill_id TEXT,
          model TEXT,
          failure_class TEXT,
          started_at TEXT NOT NULL,
          ended_at TEXT,
          UNIQUE(thread_id, attempt_number)
        );
        CREATE TABLE IF NOT EXISTS provider_attempts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          thread_id TEXT NOT NULL,
          provider_profile TEXT,
          model TEXT,
          timeout REAL,
          retry_count INTEGER NOT NULL DEFAULT 0,
          fallback INTEGER NOT NULL DEFAULT 0,
          fallback_reason TEXT,
          status TEXT NOT NULL,
          error_summary TEXT,
          metadata_json TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_locks (
          thread_id TEXT PRIMARY KEY,
          owner TEXT NOT NULL,
          status TEXT NOT NULL,
          heartbeat_at TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          takeover_count INTEGER NOT NULL DEFAULT 0,
          takeover_metadata_json TEXT,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS side_effect_ledger (
          idempotency_key TEXT PRIMARY KEY,
          thread_id TEXT NOT NULL,
          checkpoint_id TEXT NOT NULL,
          node TEXT NOT NULL,
          tool TEXT NOT NULL,
          args_hash TEXT NOT NULL,
          status TEXT NOT NULL,
          result_hash TEXT,
          result_summary_json TEXT,
          external_ref TEXT,
          audit_ref TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_projections (
          thread_id TEXT PRIMARY KEY,
          status TEXT NOT NULL,
          prompt TEXT NOT NULL,
          provider_metadata_json TEXT NOT NULL,
          fixture TEXT,
          skill_metadata_json TEXT,
          workflow_name TEXT,
          project_root TEXT,
          model TEXT,
          fixture_fallback INTEGER NOT NULL DEFAULT 0,
          latest_seq INTEGER NOT NULL DEFAULT 0,
          failure_class TEXT,
          repair_required INTEGER NOT NULL DEFAULT 0,
          pending_interrupt_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS repair_notes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          thread_id TEXT NOT NULL,
          source TEXT NOT NULL,
          note TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runtime_checkpoints (
          thread_id TEXT NOT NULL,
          checkpoint_id TEXT NOT NULL,
          state_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(thread_id, checkpoint_id)
        );
        CREATE TABLE IF NOT EXISTS skill_package_cache (
          skill_id TEXT NOT NULL,
          source_key TEXT NOT NULL,
          path TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 0,
          metadata_json TEXT NOT NULL,
          diagnostics_json TEXT,
          discovered_at TEXT NOT NULL,
          PRIMARY KEY(skill_id, source_key, path)
        );
        CREATE TABLE IF NOT EXISTS project_roots (
          root_id TEXT PRIMARY KEY,
          root_path TEXT NOT NULL,
          status TEXT NOT NULL,
          file_count INTEGER NOT NULL DEFAULT 0,
          chunk_count INTEGER NOT NULL DEFAULT 0,
          skipped_count INTEGER NOT NULL DEFAULT 0,
          omitted_count INTEGER NOT NULL DEFAULT 0,
          last_refresh_at TEXT,
          metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS project_files (
          root_id TEXT NOT NULL,
          path TEXT NOT NULL,
          size INTEGER NOT NULL,
          mtime REAL NOT NULL,
          content_hash TEXT,
          skipped_reason TEXT,
          indexed_at TEXT NOT NULL,
          PRIMARY KEY(root_id, path)
        );
        CREATE TABLE IF NOT EXISTS project_chunks (
          chunk_id TEXT PRIMARY KEY,
          root_id TEXT NOT NULL,
          path TEXT NOT NULL,
          start_line INTEGER NOT NULL,
          end_line INTEGER NOT NULL,
          start_byte INTEGER NOT NULL,
          end_byte INTEGER NOT NULL,
          content_hash TEXT,
          language TEXT,
          content TEXT NOT NULL,
          indexed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS retrieval_traces (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          thread_id TEXT,
          root_id TEXT,
          query TEXT NOT NULL,
          results_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS run_context_traces (
          thread_id TEXT PRIMARY KEY,
          trace_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_records (
          id TEXT PRIMARY KEY,
          scope TEXT NOT NULL,
          type TEXT NOT NULL,
          status TEXT NOT NULL,
          text TEXT NOT NULL,
          tags_json TEXT NOT NULL,
          confidence REAL NOT NULL,
          source_json TEXT NOT NULL,
          project_root_id TEXT,
          thread_id TEXT,
          merged_ids_json TEXT,
          last_used_at TEXT,
          expires_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          memory_id TEXT,
          action TEXT NOT NULL,
          summary TEXT,
          metadata_json TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_citations (
          citation_id TEXT PRIMARY KEY,
          memory_id TEXT NOT NULL,
          thread_id TEXT NOT NULL,
          score REAL NOT NULL,
          reasons_json TEXT NOT NULL,
          source_summary TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_tombstones (
          memory_id TEXT PRIMARY KEY,
          reason TEXT,
          metadata_json TEXT,
          deleted_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_retrieval_traces (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          thread_id TEXT,
          query TEXT NOT NULL,
          filters_json TEXT,
          selected_ids_json TEXT NOT NULL,
          omitted_ids_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_candidates (
          id TEXT PRIMARY KEY,
          thread_id TEXT,
          status TEXT NOT NULL,
          suggested_scope TEXT NOT NULL,
          suggested_type TEXT NOT NULL,
          text TEXT NOT NULL,
          confidence REAL NOT NULL,
          reason TEXT NOT NULL,
          risk TEXT NOT NULL,
          guard_json TEXT NOT NULL,
          duplicate_ids_json TEXT NOT NULL,
          source_json TEXT NOT NULL,
          created_memory_id TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_candidate_decisions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          candidate_id TEXT NOT NULL,
          decision TEXT NOT NULL,
          memory_id TEXT,
          metadata_json TEXT,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_records (
          id TEXT PRIMARY KEY,
          action TEXT NOT NULL,
          status TEXT NOT NULL,
          decision TEXT,
          thread_id TEXT,
          conversation_id TEXT,
          turn_id TEXT,
          provider TEXT,
          model TEXT,
          tool TEXT,
          skill_id TEXT,
          memory_id TEXT,
          project_root TEXT,
          metadata_json TEXT NOT NULL,
          summary TEXT,
          redacted INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_audit_thread ON audit_records(thread_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_conversation ON audit_records(conversation_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_records(project_root, created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_memory ON audit_records(memory_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_records(action, status, created_at);
        INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (1, datetime('now'));
        """
    )
    _ensure_column(conn, "run_projections", "conversation_id", "TEXT")
    _ensure_column(conn, "run_projections", "turn_id", "TEXT")
    _ensure_column(conn, "run_projections", "user_message_id", "TEXT")
    _ensure_column(conn, "run_projections", "assistant_message_id", "TEXT")
    _ensure_column(conn, "run_projections", "transcript_status", "TEXT")
    _ensure_column(conn, "run_projections", "active_head_message_id", "TEXT")
    _ensure_column(conn, "run_projections", "branch_metadata_json", "TEXT")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
          id TEXT PRIMARY KEY,
          title TEXT,
          status TEXT NOT NULL,
          archived INTEGER NOT NULL DEFAULT 0,
          active_head_message_id TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversation_turns (
          turn_id TEXT PRIMARY KEY,
          conversation_id TEXT NOT NULL,
          thread_id TEXT,
          user_message_id TEXT,
          assistant_message_id TEXT,
          status TEXT NOT NULL,
          prompt TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transcript_messages (
          id TEXT PRIMARY KEY,
          conversation_id TEXT NOT NULL,
          turn_id TEXT,
          thread_id TEXT,
          parent_message_id TEXT,
          logical_parent_message_id TEXT,
          role TEXT NOT NULL,
          status TEXT NOT NULL,
          branch_status TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transcript_parts (
          id TEXT PRIMARY KEY,
          message_id TEXT NOT NULL,
          conversation_id TEXT NOT NULL,
          turn_id TEXT,
          thread_id TEXT,
          kind TEXT NOT NULL,
          seq INTEGER NOT NULL,
          text TEXT NOT NULL,
          payload_json TEXT,
          visible INTEGER NOT NULL DEFAULT 1,
          token_estimate INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversation_run_links (
          conversation_id TEXT NOT NULL,
          turn_id TEXT NOT NULL,
          thread_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(conversation_id, turn_id, thread_id)
        );
        CREATE TABLE IF NOT EXISTS transcript_context_traces (
          thread_id TEXT PRIMARY KEY,
          conversation_id TEXT NOT NULL,
          turn_id TEXT,
          trace_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversation_compaction_summaries (
          id TEXT PRIMARY KEY,
          conversation_id TEXT NOT NULL,
          source_first_message_id TEXT,
          source_last_message_id TEXT,
          source_message_ids_json TEXT NOT NULL,
          source_turn_ids_json TEXT NOT NULL,
          replacement_ids_json TEXT NOT NULL,
          source_hash TEXT NOT NULL,
          tail_start_message_id TEXT,
          summary TEXT NOT NULL,
          source_token_estimate INTEGER NOT NULL DEFAULT 0,
          summary_token_estimate INTEGER NOT NULL DEFAULT 0,
          summarizer_json TEXT NOT NULL,
          status TEXT NOT NULL,
          stale_reason TEXT,
          previous_summary_id TEXT,
          trigger TEXT NOT NULL DEFAULT 'manual',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tool_output_replacements (
          id TEXT PRIMARY KEY,
          conversation_id TEXT NOT NULL,
          turn_id TEXT,
          thread_id TEXT,
          message_id TEXT NOT NULL,
          part_id TEXT,
          tool_name TEXT NOT NULL,
          output_hash TEXT NOT NULL,
          summary TEXT NOT NULL,
          omitted_char_count INTEGER NOT NULL DEFAULT 0,
          reason TEXT NOT NULL,
          retention_policy TEXT NOT NULL,
          status TEXT NOT NULL,
          redacted_reference_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_conversation_turns_conversation ON conversation_turns(conversation_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_transcript_messages_conversation ON transcript_messages(conversation_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_transcript_parts_message ON transcript_parts(message_id, seq);
        CREATE INDEX IF NOT EXISTS idx_conversation_run_links_thread ON conversation_run_links(thread_id);
        CREATE INDEX IF NOT EXISTS idx_compaction_conversation_status ON conversation_compaction_summaries(conversation_id, status, created_at);
        CREATE INDEX IF NOT EXISTS idx_compaction_source_range ON conversation_compaction_summaries(conversation_id, source_first_message_id, source_last_message_id);
        CREATE INDEX IF NOT EXISTS idx_replacements_conversation_status ON tool_output_replacements(conversation_id, status, created_at);
        CREATE INDEX IF NOT EXISTS idx_replacements_source_part ON tool_output_replacements(part_id);
        CREATE INDEX IF NOT EXISTS idx_replacements_thread ON tool_output_replacements(thread_id);
        """
    )
    _ensure_column(conn, "conversations", "forked_from_conversation_id", "TEXT")
    _ensure_column(conn, "conversations", "forked_from_message_id", "TEXT")
    _ensure_column(conn, "conversations", "forked_from_turn_id", "TEXT")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversation_branch_records (
          id TEXT PRIMARY KEY,
          operation TEXT NOT NULL,
          source_conversation_id TEXT NOT NULL,
          target_conversation_id TEXT NOT NULL,
          source_message_id TEXT,
          source_turn_id TEXT,
          previous_active_head_id TEXT,
          new_active_head_id TEXT,
          reason_json TEXT NOT NULL,
          status TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversation_active_head_transitions (
          id TEXT PRIMARY KEY,
          conversation_id TEXT NOT NULL,
          operation TEXT NOT NULL,
          previous_active_head_id TEXT,
          new_active_head_id TEXT,
          branch_record_id TEXT,
          reason_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_branch_records_source ON conversation_branch_records(source_conversation_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_branch_records_target ON conversation_branch_records(target_conversation_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_active_head_transitions_conversation ON conversation_active_head_transitions(conversation_id, created_at);
        """
    )


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(value: str | None) -> Any:
    if value is None:
        return None
    return json.loads(value)


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for key in (
        "provider_metadata_json",
        "skill_metadata_json",
        "pending_interrupt_json",
        "metadata_json",
        "takeover_metadata_json",
        "source_json",
        "reasons_json",
        "filters_json",
        "selected_ids_json",
        "omitted_ids_json",
        "guard_json",
        "duplicate_ids_json",
        "tags_json",
        "merged_ids_json",
        "payload_json",
        "trace_json",
        "source_message_ids_json",
        "source_turn_ids_json",
        "replacement_ids_json",
        "summarizer_json",
        "redacted_reference_json",
        "reason_json",
        "branch_metadata_json",
    ):
        if key in result:
            result[key.removesuffix("_json")] = _loads(result.pop(key))
    return result


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _ledger_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    result = _row_dict(row)
    if result is None:
        return None
    if "result_summary_json" in result:
        result["result_summary"] = _loads(result.pop("result_summary_json"))
    return result
