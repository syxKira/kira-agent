from __future__ import annotations

import shutil
import sys
from typing import Any

from kira_server.providers.config import ProviderConfigStore, redact_text
from kira_server.safety import PermissionService, redact_value
from kira_server.storage.database import RuntimeStorage, utc_now


def doctor_report(
    *,
    storage: RuntimeStorage,
    provider_config: ProviderConfigStore,
    skill_registry,
    project_knowledge,
    deep_provider: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    providers = provider_config.readiness_metadata()
    has_real_key = any(provider.get("has_api_key") for provider in providers.get("providers", {}).values())
    checks.append(
        _check(
            "provider",
            "ok" if has_real_key else "warning",
            "Real provider config is ready" if has_real_key else "No valid real provider key configured; fixture fallback is available",
            remediation=None if has_real_key else "Configure ~/.kira-agent/config.yaml or continue with fixture mode",
            evidence={
                "loaded": providers.get("loaded"),
                "config_path": providers.get("config_path"),
                "default_provider": providers.get("default_provider"),
                "provider_count": len(providers.get("providers", {})),
                "has_api_key": has_real_key,
                "provider_smoke": "skipped" if not deep_provider else "not_implemented_stage_09",
            },
        )
    )
    db_ok = _runtime_db_ok(storage)
    checks.append(_check("runtime_storage", "ok" if db_ok else "error", "Runtime SQLite storage is available" if db_ok else "Runtime SQLite storage check failed"))
    checks.append(_check("python", "ok", "Python runtime is available", evidence={"executable": sys.executable, "version": sys.version.split()[0]}))
    rg_path = shutil.which("rg")
    checks.append(
        _check(
            "rg",
            "ok" if rg_path else "warning",
            "`rg` is available" if rg_path else "`rg` is not available; Python fallback will be used",
            remediation=None if rg_path else "Install ripgrep for faster local search",
            evidence={"path": rg_path},
        )
    )
    try:
        skills = skill_registry.metadata().get("skills", [])
        invalid = [skill for skill in skills if skill.get("valid") is False]
        checks.append(
            _check(
                "skills",
                "warning" if invalid else "ok",
                f"{len(invalid)} invalid skill manifests" if invalid else "Skill manifests are readable",
                evidence={"skill_count": len(skills), "invalid_count": len(invalid)},
            )
        )
    except Exception as exc:
        checks.append(_check("skills", "error", "Skill diagnostics failed", evidence={"error": redact_text(str(exc))}))
    try:
        project_status = project_knowledge.status(None)
        checks.append(
            _check(
                "project_index",
                "ok" if project_status.get("status") in {"ready", "not_indexed"} else "warning",
                f"Project index status: {project_status.get('status')}",
                evidence=project_status,
            )
        )
    except Exception as exc:
        checks.append(_check("project_index", "warning", "Project index diagnostics failed", evidence={"error": redact_text(str(exc))}))
    checks.append(_table_check(storage, "memory_records", "memory_db", "Memory database tables are available"))
    checks.append(_table_check(storage, "run_locks", "run_locks", "Run lock table is available"))
    checks.append(_table_check(storage, "side_effect_ledger", "side_effect_ledger", "Side-effect ledger table is available"))
    checks.append(_table_check(storage, "audit_records", "audit_storage", "Audit table is available"))
    for diagnostic in storage.audit_diagnostics[-5:]:
        checks.append(redact_value(diagnostic))
    status = "error" if any(check["status"] == "error" for check in checks) else ("warning" if any(check["status"] == "warning" for check in checks) else "ok")
    return {
        "status": status,
        "generated_at": utc_now(),
        "checks": redact_value(checks),
        "versions": {"backend": "0.1.0", "frontend": "vite-local"},
        "deep_checks": {"provider_smoke": "requested" if deep_provider else "skipped"},
    }


def run_trace_export(storage: RuntimeStorage, thread_id: str, *, limit: int = 100) -> dict[str, Any] | None:
    state = storage.state_projection(thread_id)
    if state is None:
        return None
    events = [event.model_dump() for event in storage.list_events(thread_id)]
    limited_events = events[: max(1, min(limit, 500))]
    return redact_value(
        {
            "scope": "run",
            "thread_id": thread_id,
            "generated_at": utc_now(),
            "redacted": True,
            "truncated": len(events) > len(limited_events),
            "limit": limit,
            "state": state,
            "events": limited_events,
            "audit": storage.list_audit_records(thread_id=thread_id, limit=limit),
            "context": state.get("context_trace"),
            "provider_attempts": state.get("provider_attempts") or [],
            "side_effects": state.get("side_effects") or [],
        }
    )


def conversation_trace_export(storage: RuntimeStorage, transcript_service, conversation_id: str, *, limit: int = 100) -> dict[str, Any] | None:
    conversation = transcript_service.get_conversation(conversation_id)
    if conversation is None:
        return None
    context = transcript_service.context_for_conversation(conversation_id)
    messages = transcript_service.transcript(conversation_id)[: max(1, min(limit, 500))]
    return redact_value(
        {
            "scope": "conversation",
            "conversation_id": conversation_id,
            "generated_at": utc_now(),
            "redacted": True,
            "truncated": len(messages) >= limit,
            "limit": limit,
            "transcript": {
                "conversation": conversation.model_dump(),
                "messages": [message.model_dump() for message in messages],
                "context_trace": context.trace,
                "branch_records": [record.model_dump() for record in transcript_service.list_branch_records(conversation_id)],
                "compaction_summaries": [summary.model_dump() for summary in transcript_service.list_compaction_summaries(conversation_id)],
                "tool_output_replacements": [replacement.model_dump() for replacement in transcript_service.list_tool_output_replacements(conversation_id=conversation_id)],
            },
            "audit": storage.list_audit_records(conversation_id=conversation_id, limit=limit),
        }
    )


def project_trace_export(storage: RuntimeStorage, root_id: str | None = None, *, limit: int = 100) -> dict[str, Any]:
    clauses = []
    params: list[Any] = []
    if root_id:
        clauses.append("root_id = ?")
        params.append(root_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 500)))
    with storage.database.connect() as conn:
        rows = conn.execute(f"SELECT * FROM retrieval_traces {where} ORDER BY created_at DESC LIMIT ?", params).fetchall()
    traces = []
    for row in rows:
        traces.append({"id": row["id"], "thread_id": row["thread_id"], "root_id": row["root_id"], "query": row["query"], "results": _loads_json(row["results_json"]), "created_at": row["created_at"]})
    return redact_value({"scope": "project", "root_id": root_id, "generated_at": utc_now(), "redacted": True, "truncated": len(traces) >= limit, "limit": limit, "project": {"retrieval_traces": traces}, "audit": storage.list_audit_records(project_root=root_id, limit=limit)})


def memory_trace_export(storage: RuntimeStorage, memory_id: str | None = None, *, thread_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    with storage.database.connect() as conn:
        citation_rows = conn.execute(
            "SELECT * FROM memory_citations WHERE (? IS NULL OR memory_id = ?) AND (? IS NULL OR thread_id = ?) ORDER BY created_at DESC LIMIT ?",
            (memory_id, memory_id, thread_id, thread_id, max(1, min(limit, 500))),
        ).fetchall()
        trace_rows = conn.execute(
            "SELECT * FROM memory_retrieval_traces WHERE (? IS NULL OR thread_id = ?) ORDER BY created_at DESC LIMIT ?",
            (thread_id, thread_id, max(1, min(limit, 500))),
        ).fetchall()
    citations = [dict(row) for row in citation_rows]
    traces = [dict(row) for row in trace_rows]
    return redact_value({"scope": "memory", "memory_id": memory_id, "thread_id": thread_id, "generated_at": utc_now(), "redacted": True, "truncated": len(citations) >= limit, "limit": limit, "memory": {"citations": citations, "retrieval_traces": traces}, "audit": storage.list_audit_records(memory_id=memory_id, thread_id=thread_id, limit=limit)})


def replacement_inspection(storage: RuntimeStorage, transcript_service, replacement_id: str, permission_service: PermissionService) -> dict[str, Any]:
    replacements = transcript_service.list_tool_output_replacements()
    replacement = next((item for item in replacements if item.id == replacement_id), None)
    if replacement is None:
        return {"replacement_id": replacement_id, "status": "missing", "content": None, "reason": "replacement_not_found", "redacted": True, "audit_id": None, "metadata": {}}
    permission = permission_service.evaluate("replacement.inspect", {"replacement_id": replacement.id, "retention_policy": replacement.retention_policy, "reason": replacement.reason})
    status = "allowed" if permission.decision == "allow" else "denied"
    audit = storage.record_audit(
        action="replacement.inspect",
        status=status,
        decision=permission.decision,
        thread_id=replacement.thread_id,
        conversation_id=replacement.conversation_id,
        turn_id=replacement.turn_id,
        tool=replacement.tool_name,
        metadata={"replacement_id": replacement.id, "reason": replacement.reason, "retention_policy": replacement.retention_policy},
        summary="Replacement inspection allowed" if status == "allowed" else "Replacement inspection denied by policy",
    )
    return redact_value(
        {
            "replacement_id": replacement.id,
            "status": status,
            "content": replacement.summary if status == "allowed" else None,
            "reason": None if status == "allowed" else "; ".join(permission.reasons),
            "redacted": True,
            "audit_id": audit["id"],
            "metadata": {
                "hash_prefix": replacement.output_hash[:16],
                "omitted_char_count": replacement.omitted_char_count,
                "reason": replacement.reason,
                "retention_policy": replacement.retention_policy,
            },
            "permission": permission.model_dump(),
        }
    )


def _check(component: str, status: str, message: str, *, remediation: str | None = None, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"component": component, "status": status, "severity": "error" if status == "error" else ("warning" if status == "warning" else "info"), "message": redact_text(message) or message, "remediation": remediation, "evidence": redact_value(evidence or {})}


def _runtime_db_ok(storage: RuntimeStorage) -> bool:
    try:
        with storage.database.connect() as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        return False


def _table_check(storage: RuntimeStorage, table: str, component: str, message: str) -> dict[str, Any]:
    try:
        with storage.database.connect() as conn:
            count = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
        return _check(component, "ok", message, evidence={"record_count": int(count)})
    except Exception as exc:
        return _check(component, "warning", f"{component} diagnostics failed", evidence={"error": redact_text(str(exc))})


def _loads_json(value: str | None) -> Any:
    if value is None:
        return None
    import json

    return json.loads(value)
