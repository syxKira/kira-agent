from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from kira_server.context import Citation, ContextItem, estimate_budget_cost, make_context_id
from kira_server.providers.config import redact_text
from kira_server.storage.database import RuntimeStorage, utc_now


MemoryScope = Literal["session", "projectLocal", "project", "user"]
MemoryType = Literal["preference", "feedback", "decision", "project", "reference", "fact", "workflow"]
MemoryStatus = Literal["active", "stale", "archived"]
CandidateStatus = Literal["pending", "approved", "rejected", "deferred", "blocked"]


SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "api_key": re.compile(r"\b(?:sk|rk|ak)-[A-Za-z0-9_\-]{12,}\b|api[_-]?key\s*[:=]\s*['\"]?[^'\"\s]{8,}", re.IGNORECASE),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{12,}\b", re.IGNORECASE),
    "cookie": re.compile(r"\b(cookie|set-cookie)\s*[:=]\s*[^;\n]{8,}", re.IGNORECASE),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "env_secret": re.compile(r"(?m)^\s*[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|API_KEY)[A-Z0-9_]*\s*=\s*.+$"),
    "raw_provider_config": re.compile(r"\b(baseURL|base_url|authorization|apiKey|api_key)\b", re.IGNORECASE),
    "provider_error": re.compile(r"\b(provider_http_error|provider_timeout|upstream error|authorization failed)\b", re.IGNORECASE),
    "high_risk_personal": re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b(?:customer|passport|credit card)\s*[:#]", re.IGNORECASE),
}


class GuardResult(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    redacted_text: str = ""


class MemorySource(BaseModel):
    kind: str = "manual"
    summary: str = ""
    thread_id: str | None = None
    project_root_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryRecord(BaseModel):
    id: str
    scope: MemoryScope
    type: MemoryType
    status: MemoryStatus = "active"
    text: str = Field(min_length=1, max_length=20_000)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)
    source: MemorySource = Field(default_factory=MemorySource)
    created_at: str
    updated_at: str
    last_used_at: str | None = None
    expires_at: str | None = None
    project_root_id: str | None = None
    thread_id: str | None = None
    merged_ids: list[str] = Field(default_factory=list)

    @property
    def injectable(self) -> bool:
        return self.status == "active" and not is_expired(self.expires_at)


class MemoryCreateRequest(BaseModel):
    scope: MemoryScope = "projectLocal"
    type: MemoryType = "fact"
    status: MemoryStatus = "active"
    text: str = Field(min_length=1, max_length=20_000)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)
    source: MemorySource = Field(default_factory=MemorySource)
    expires_at: str | None = None
    project_root_id: str | None = None
    thread_id: str | None = None


class MemoryUpdateRequest(BaseModel):
    scope: MemoryScope | None = None
    type: MemoryType | None = None
    status: MemoryStatus | None = None
    text: str | None = Field(default=None, min_length=1, max_length=20_000)
    tags: list[str] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: MemorySource | None = None
    expires_at: str | None = None
    project_root_id: str | None = None
    thread_id: str | None = None


class MemorySearchRequest(BaseModel):
    query: str = ""
    scopes: list[MemoryScope] = Field(default_factory=list)
    types: list[MemoryType] = Field(default_factory=list)
    statuses: list[MemoryStatus] = Field(default_factory=lambda: ["active"])
    tags: list[str] = Field(default_factory=list)
    project_root_id: str | None = None
    thread_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=50)
    include_non_injectable: bool = False


class ScoreReason(BaseModel):
    factor: str
    score: float
    matched: list[str] = Field(default_factory=list)


class MemoryRetrievalResult(BaseModel):
    memory: MemoryRecord
    score: float
    score_reasons: list[ScoreReason]
    duplicate_ids: list[str] = Field(default_factory=list)
    citation_id: str | None = None


class MemorySearchResponse(BaseModel):
    query: str
    results: list[MemoryRetrievalResult]
    omitted_count: int
    filters: dict[str, Any] = Field(default_factory=dict)


class MemoryActionRequest(BaseModel):
    action: Literal["archive", "delete", "merge", "refresh", "stale", "promote", "explain"]
    target_scope: MemoryScope | None = None
    merge_ids: list[str] = Field(default_factory=list)
    evidence: str | None = None
    approved: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryCandidate(BaseModel):
    id: str
    thread_id: str | None = None
    status: CandidateStatus = "pending"
    suggested_scope: MemoryScope = "projectLocal"
    suggested_type: MemoryType = "fact"
    text: str
    confidence: float = Field(ge=0, le=1)
    reason: str
    risk: str = "low"
    guard: GuardResult
    duplicate_ids: list[str] = Field(default_factory=list)
    source: MemorySource = Field(default_factory=MemorySource)
    created_memory_id: str | None = None
    created_at: str
    updated_at: str


class ExtractionRequest(BaseModel):
    thread_id: str | None = None
    prompt: str | None = None
    feedback: str | None = None
    mode: Literal["fixture", "real", "auto"] = "auto"
    dry_run: bool = True


@dataclass(frozen=True)
class MemoryContextResult:
    items: list[ContextItem]
    trace: dict[str, Any]


class MemoryService:
    def __init__(self, storage: RuntimeStorage) -> None:
        self.storage = storage

    def create(self, request: MemoryCreateRequest) -> MemoryRecord:
        guard = guard_memory_text(_guard_text(request.text, request.source.model_dump()))
        if not guard.allowed:
            self._append_event(None, "guard_rejected", "Rejected unsafe memory write", {"reasons": guard.reasons})
            raise ValueError(f"memory_guard_rejected:{','.join(guard.reasons)}")
        now = utc_now()
        record = MemoryRecord(
            id=f"mem_{uuid4().hex}",
            scope=request.scope,
            type=request.type,
            status=request.status,
            text=redact_text(request.text),
            tags=_normalize_tags(request.tags),
            confidence=request.confidence,
            source=_redacted_source(request.source),
            created_at=now,
            updated_at=now,
            expires_at=request.expires_at,
            project_root_id=request.project_root_id or request.source.project_root_id,
            thread_id=request.thread_id or request.source.thread_id,
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_records(
                  id, scope, type, status, text, tags_json, confidence, source_json,
                  project_root_id, thread_id, merged_ids_json, last_used_at, expires_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _record_params(record),
            )
        self._append_event(record.id, "create", "Memory created", {"scope": record.scope, "type": record.type})
        return record

    def get(self, memory_id: str) -> MemoryRecord | None:
        with self.storage.database.connect() as conn:
            row = conn.execute("SELECT * FROM memory_records WHERE id = ?", (memory_id,)).fetchone()
        return _record_from_row(row) if row else None

    def list(self, request: MemorySearchRequest | None = None) -> list[MemoryRecord]:
        filters = request or MemorySearchRequest(statuses=[])
        records = self._all_records()
        return [record for record in records if self._matches_filters(record, filters, for_injection=False)]

    def update(self, memory_id: str, request: MemoryUpdateRequest) -> MemoryRecord | None:
        current = self.get(memory_id)
        if current is None:
            return None
        next_text = request.text if request.text is not None else current.text
        source = request.source or current.source
        guard = guard_memory_text(_guard_text(next_text, source.model_dump(), request.model_dump(exclude_none=True)))
        if not guard.allowed:
            self._append_event(memory_id, "guard_rejected", "Rejected unsafe memory update", {"reasons": guard.reasons})
            raise ValueError(f"memory_guard_rejected:{','.join(guard.reasons)}")
        updated = current.model_copy(
            update={
                "scope": request.scope or current.scope,
                "type": request.type or current.type,
                "status": request.status or current.status,
                "text": redact_text(next_text),
                "tags": _normalize_tags(request.tags if request.tags is not None else current.tags),
                "confidence": request.confidence if request.confidence is not None else current.confidence,
                "source": _redacted_source(source),
                "expires_at": request.expires_at if request.expires_at is not None else current.expires_at,
                "project_root_id": request.project_root_id if request.project_root_id is not None else current.project_root_id,
                "thread_id": request.thread_id if request.thread_id is not None else current.thread_id,
                "updated_at": utc_now(),
            }
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                UPDATE memory_records
                SET scope = ?, type = ?, status = ?, text = ?, tags_json = ?, confidence = ?,
                    source_json = ?, project_root_id = ?, thread_id = ?, merged_ids_json = ?,
                    last_used_at = ?, expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    updated.scope,
                    updated.type,
                    updated.status,
                    updated.text,
                    _json(updated.tags),
                    updated.confidence,
                    _json(updated.source.model_dump()),
                    updated.project_root_id,
                    updated.thread_id,
                    _json(updated.merged_ids),
                    updated.last_used_at,
                    updated.expires_at,
                    updated.updated_at,
                    updated.id,
                ),
            )
        self._append_event(memory_id, "update", "Memory updated", {"scope": updated.scope, "type": updated.type})
        return updated

    def delete(self, memory_id: str, *, reason: str = "deleted") -> bool:
        record = self.get(memory_id)
        if record is None:
            return False
        now = utc_now()
        with self.storage.database.connect() as conn:
            conn.execute("DELETE FROM memory_records WHERE id = ?", (memory_id,))
            conn.execute(
                """
                INSERT INTO memory_tombstones(memory_id, reason, metadata_json, deleted_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET reason=excluded.reason, metadata_json=excluded.metadata_json, deleted_at=excluded.deleted_at
                """,
                (memory_id, redact_text(reason), _json({"scope": record.scope, "type": record.type}), now),
            )
        self._append_event(memory_id, "delete", "Memory deleted", {"reason": reason})
        return True

    def search(self, request: MemorySearchRequest, *, thread_id: str | None = None, inject: bool = False) -> MemorySearchResponse:
        records = [record for record in self._all_records() if self._matches_filters(record, request, for_injection=inject)]
        scored = [score_memory(record, request.query, request) for record in records]
        scored = [result for result in scored if result.score > 0 or not request.query.strip()]
        deduped, duplicate_ids = _dedupe_results(scored)
        for result in deduped:
            result.duplicate_ids.extend(duplicate_ids.get(result.memory.id, []))
        ranked = sorted(deduped, key=lambda item: (-item.score, item.memory.updated_at, item.memory.id))[: request.top_k]
        omitted = max(len(scored) - len(ranked), 0)
        self._record_retrieval_trace(thread_id, request, ranked, [item.memory.id for item in scored if item not in ranked])
        return MemorySearchResponse(query=request.query, results=ranked, omitted_count=omitted, filters=request.model_dump())

    def context_items_for_run(
        self,
        *,
        thread_id: str,
        query: str,
        scopes: list[MemoryScope] | None = None,
        types: list[MemoryType] | None = None,
        top_k: int = 5,
        project_root_id: str | None = None,
    ) -> MemoryContextResult:
        request = MemorySearchRequest(
            query=query,
            scopes=scopes or [],
            types=types or [],
            statuses=["active"],
            project_root_id=project_root_id,
            thread_id=thread_id,
            top_k=top_k,
        )
        response = self.search(request, thread_id=thread_id, inject=True)
        items: list[ContextItem] = []
        citation_summaries: list[dict[str, Any]] = []
        for result in response.results:
            citation_id = self._create_citation(thread_id, result)
            result.citation_id = citation_id
            citation_summaries.append({"citation_id": citation_id, "memory_id": result.memory.id, "score": result.score})
            items.append(context_item_from_memory(result, citation_id))
            self._touch_memory(result.memory.id)
        trace = {
            "query": query,
            "result_count": len(items),
            "omitted_count": response.omitted_count,
            "citations": citation_summaries,
            "results": [result.model_dump() for result in response.results],
        }
        return MemoryContextResult(items=items, trace=trace)

    def action(self, memory_id: str, request: MemoryActionRequest) -> dict[str, Any] | None:
        record = self.get(memory_id)
        if record is None:
            return None
        if request.action == "explain":
            result = score_memory(record, request.evidence or record.text, MemorySearchRequest(query=request.evidence or record.text, statuses=[]))
            return {"memory": record.model_dump(), "explanation": result.model_dump()}
        if request.action == "archive":
            updated = self.update(memory_id, MemoryUpdateRequest(status="archived"))
            return {"memory": updated.model_dump() if updated else None}
        if request.action == "stale":
            updated = self.update(memory_id, MemoryUpdateRequest(status="stale"))
            return {"memory": updated.model_dump() if updated else None}
        if request.action == "delete":
            return {"deleted": self.delete(memory_id, reason=str(request.metadata.get("reason") or "deleted"))}
        if request.action == "refresh":
            guard = guard_memory_text(request.evidence or "")
            if not guard.allowed:
                raise ValueError(f"memory_guard_rejected:{','.join(guard.reasons)}")
            source = record.source.model_copy(update={"summary": redact_text(request.evidence or record.source.summary)})
            updated = self.update(memory_id, MemoryUpdateRequest(source=source, confidence=min(record.confidence + 0.05, 1.0)))
            self._append_event(memory_id, "refresh", "Memory refreshed", {"evidence": redact_text(request.evidence)})
            return {"memory": updated.model_dump() if updated else None}
        if request.action == "promote":
            target = request.target_scope
            if target in {"project", "user"} and not request.approved:
                return {
                    "approval_required": True,
                    "interrupt": {
                        "kind": "approval",
                        "title": "Approve memory promotion",
                        "body": f"Promote memory to {target}",
                        "data": {"memory_id": memory_id, "target_scope": target},
                    },
                }
            updated = self.update(memory_id, MemoryUpdateRequest(scope=target or record.scope))
            self._append_event(memory_id, "promote", "Memory promoted", {"target_scope": target})
            return {"memory": updated.model_dump() if updated else None, "approval_required": False}
        if request.action == "merge":
            merged_ids = [merge_id for merge_id in request.merge_ids if merge_id != memory_id]
            merged_records = [self.get(merge_id) for merge_id in merged_ids]
            merged_text = record.text
            merged_tags = set(record.tags)
            for other in merged_records:
                if other is None:
                    continue
                merged_tags.update(other.tags)
                if other.text not in merged_text:
                    merged_text = f"{merged_text}\n{other.text}"
                self.update(other.id, MemoryUpdateRequest(status="archived"))
            updated = record.model_copy(update={"text": merged_text, "tags": sorted(merged_tags), "merged_ids": sorted(set(record.merged_ids + merged_ids)), "updated_at": utc_now()})
            guard = guard_memory_text(updated.text)
            if not guard.allowed:
                raise ValueError(f"memory_guard_rejected:{','.join(guard.reasons)}")
            self.update(memory_id, MemoryUpdateRequest(text=updated.text, tags=updated.tags))
            with self.storage.database.connect() as conn:
                conn.execute("UPDATE memory_records SET merged_ids_json = ? WHERE id = ?", (_json(updated.merged_ids), memory_id))
            self._append_event(memory_id, "merge", "Memory merged", {"merged_ids": merged_ids})
            return {"memory": self.get(memory_id).model_dump(), "merged_ids": merged_ids}
        raise ValueError(f"unsupported_action:{request.action}")

    def extract(self, request: ExtractionRequest) -> dict[str, Any]:
        source_text = " ".join(part for part in [request.prompt, request.feedback] if part)
        if not source_text and request.thread_id:
            state = self.storage.state_projection(request.thread_id)
            source_text = str((state or {}).get("prompt") or "")
        if not source_text.strip():
            return {"status": "skipped", "reason": "no_extractable_input", "candidates": []}
        candidate_text = _candidate_text(source_text)
        guard = guard_memory_text(candidate_text)
        duplicate_ids = [result.memory.id for result in self.search(MemorySearchRequest(query=candidate_text, top_k=5), thread_id=request.thread_id).results if _normalize(result.memory.text) == _normalize(candidate_text)]
        status: CandidateStatus = "blocked" if not guard.allowed else "pending"
        now = utc_now()
        candidate = MemoryCandidate(
            id=f"cand_{uuid4().hex}",
            thread_id=request.thread_id,
            status=status,
            suggested_scope="projectLocal",
            suggested_type=_candidate_type(candidate_text),
            text=guard.redacted_text if guard.allowed else "[blocked by memory guard]",
            confidence=0.72 if not duplicate_ids else 0.45,
            reason="Deterministic dry-run extraction from bounded run summary",
            risk="high" if not guard.allowed else "low",
            guard=guard,
            duplicate_ids=duplicate_ids,
            source=MemorySource(kind="extraction", summary=(guard.redacted_text or redact_text(source_text[:500]))[:500], thread_id=request.thread_id),
            created_at=now,
            updated_at=now,
        )
        self._save_candidate(candidate)
        return {"status": "dry_run", "candidates": [candidate.model_dump()]}

    def list_candidates(self, thread_id: str | None = None) -> list[MemoryCandidate]:
        with self.storage.database.connect() as conn:
            if thread_id:
                rows = conn.execute("SELECT * FROM memory_candidates WHERE thread_id = ? ORDER BY created_at DESC", (thread_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM memory_candidates ORDER BY created_at DESC").fetchall()
        return [_candidate_from_row(row) for row in rows]

    def candidate_decision(self, candidate_id: str, decision: str, *, text: str | None = None) -> dict[str, Any] | None:
        candidate = self._get_candidate(candidate_id)
        if candidate is None:
            return None
        if decision == "approve":
            if candidate.status == "blocked" or not candidate.guard.allowed:
                raise ValueError("candidate_blocked")
            create = MemoryCreateRequest(
                scope=candidate.suggested_scope,
                type=candidate.suggested_type,
                text=text or candidate.text,
                confidence=candidate.confidence,
                source=candidate.source,
                thread_id=candidate.thread_id,
            )
            record = self.create(create)
            self._update_candidate(candidate_id, "approved", record.id, text=text)
            return {"candidate": self._get_candidate(candidate_id).model_dump(), "memory": record.model_dump()}
        if decision in {"reject", "defer"}:
            self._update_candidate(candidate_id, "rejected" if decision == "reject" else "deferred", None, text=text)
            return {"candidate": self._get_candidate(candidate_id).model_dump()}
        if decision == "edit":
            self._update_candidate(candidate_id, "pending", None, text=text)
            return {"candidate": self._get_candidate(candidate_id).model_dump()}
        raise ValueError(f"unsupported_candidate_decision:{decision}")

    def _all_records(self) -> list[MemoryRecord]:
        with self.storage.database.connect() as conn:
            rows = conn.execute("SELECT * FROM memory_records ORDER BY updated_at DESC, id").fetchall()
        return [_record_from_row(row) for row in rows]

    def _matches_filters(self, record: MemoryRecord, request: MemorySearchRequest, *, for_injection: bool) -> bool:
        if for_injection and not record.injectable:
            return False
        if not request.include_non_injectable and request.statuses and record.status not in request.statuses:
            return False
        if request.scopes and record.scope not in request.scopes:
            return False
        if request.types and record.type not in request.types:
            return False
        if request.project_root_id and record.project_root_id and record.project_root_id != request.project_root_id:
            return False
        if request.thread_id and record.scope == "session" and record.thread_id and record.thread_id != request.thread_id:
            return False
        if request.tags and not set(_normalize_tags(request.tags)).issubset(set(record.tags)):
            return False
        return True

    def _record_retrieval_trace(self, thread_id: str | None, request: MemorySearchRequest, selected: list[MemoryRetrievalResult], omitted_ids: list[str]) -> None:
        with self.storage.database.connect() as conn:
            conn.execute(
                "INSERT INTO memory_retrieval_traces(thread_id, query, filters_json, selected_ids_json, omitted_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (thread_id, redact_text(request.query), _json(request.model_dump()), _json([item.memory.id for item in selected]), _json(omitted_ids), utc_now()),
            )

    def _create_citation(self, thread_id: str, result: MemoryRetrievalResult) -> str:
        citation_id = f"mcit_{uuid4().hex}"
        with self.storage.database.connect() as conn:
            conn.execute(
                "INSERT INTO memory_citations(citation_id, memory_id, thread_id, score, reasons_json, source_summary, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    citation_id,
                    result.memory.id,
                    thread_id,
                    result.score,
                    _json([reason.model_dump() for reason in result.score_reasons]),
                    redact_text(result.memory.source.summary),
                    utc_now(),
                ),
            )
        self._append_event(result.memory.id, "inject", "Memory injected", {"thread_id": thread_id, "citation_id": citation_id})
        return citation_id

    def _touch_memory(self, memory_id: str) -> None:
        with self.storage.database.connect() as conn:
            conn.execute("UPDATE memory_records SET last_used_at = ?, updated_at = updated_at WHERE id = ?", (utc_now(), memory_id))

    def _append_event(self, memory_id: str | None, action: str, summary: str, metadata: dict[str, Any] | None = None) -> None:
        safe_metadata = redact_value(metadata or {})
        with self.storage.database.connect() as conn:
            conn.execute(
                "INSERT INTO memory_events(memory_id, action, summary, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (memory_id, action, redact_text(summary), _json(safe_metadata), utc_now()),
            )

    def _save_candidate(self, candidate: MemoryCandidate) -> None:
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_candidates(
                  id, thread_id, status, suggested_scope, suggested_type, text, confidence,
                  reason, risk, guard_json, duplicate_ids_json, source_json, created_memory_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.id,
                    candidate.thread_id,
                    candidate.status,
                    candidate.suggested_scope,
                    candidate.suggested_type,
                    candidate.text,
                    candidate.confidence,
                    redact_text(candidate.reason),
                    candidate.risk,
                    _json(candidate.guard.model_dump()),
                    _json(candidate.duplicate_ids),
                    _json(candidate.source.model_dump()),
                    candidate.created_memory_id,
                    candidate.created_at,
                    candidate.updated_at,
                ),
            )

    def _get_candidate(self, candidate_id: str) -> MemoryCandidate | None:
        with self.storage.database.connect() as conn:
            row = conn.execute("SELECT * FROM memory_candidates WHERE id = ?", (candidate_id,)).fetchone()
        return _candidate_from_row(row) if row else None

    def _update_candidate(self, candidate_id: str, status: CandidateStatus, memory_id: str | None, *, text: str | None = None) -> None:
        candidate = self._get_candidate(candidate_id)
        if candidate is None:
            return
        next_text = text or candidate.text
        guard = guard_memory_text(next_text)
        if not guard.allowed:
            next_text = "[blocked by memory guard]"
            status = "blocked"
        with self.storage.database.connect() as conn:
            conn.execute(
                "UPDATE memory_candidates SET status = ?, text = ?, guard_json = ?, created_memory_id = ?, updated_at = ? WHERE id = ?",
                (status, guard.redacted_text if guard.allowed else next_text, _json(guard.model_dump()), memory_id, utc_now(), candidate_id),
            )
            conn.execute(
                "INSERT INTO memory_candidate_decisions(candidate_id, decision, memory_id, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (candidate_id, status, memory_id, _json({"text_edited": text is not None}), utc_now()),
            )


def guard_memory_text(text: str) -> GuardResult:
    redacted = text or ""
    reasons = []
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(redacted):
            reasons.append(name)
            redacted = pattern.sub(f"[redacted:{name}]", redacted)
    redacted = redact_text(redacted)
    return GuardResult(allowed=not reasons, reasons=reasons, redacted_text=redacted)


def score_memory(record: MemoryRecord, query: str, request: MemorySearchRequest) -> MemoryRetrievalResult:
    query_terms = _terms(query)
    text_terms = set(_terms(record.text))
    tag_terms = set(_terms(" ".join(record.tags)))
    reasons: list[ScoreReason] = []
    score = 0.0
    matched_text = sorted(set(query_terms) & text_terms)
    if matched_text:
        value = len(matched_text) * 4.0
        score += value
        reasons.append(ScoreReason(factor="text_overlap", score=value, matched=matched_text))
    matched_tags = sorted(set(query_terms) & tag_terms)
    if matched_tags:
        value = len(matched_tags) * 3.0
        score += value
        reasons.append(ScoreReason(factor="tag_overlap", score=value, matched=matched_tags))
    if request.scopes and record.scope in request.scopes:
        score += 2.0
        reasons.append(ScoreReason(factor="scope_match", score=2.0, matched=[record.scope]))
    if request.types and record.type in request.types:
        score += 2.0
        reasons.append(ScoreReason(factor="type_match", score=2.0, matched=[record.type]))
    confidence_score = round(record.confidence * 2.0, 3)
    score += confidence_score
    reasons.append(ScoreReason(factor="confidence", score=confidence_score, matched=[]))
    if record.last_used_at:
        score += 0.5
        reasons.append(ScoreReason(factor="prior_usefulness", score=0.5, matched=[]))
    if not query_terms:
        score += 1.0
        reasons.append(ScoreReason(factor="default_active", score=1.0, matched=[]))
    return MemoryRetrievalResult(memory=record, score=round(score, 3), score_reasons=reasons)


def context_item_from_memory(result: MemoryRetrievalResult, citation_id: str) -> ContextItem:
    memory = result.memory
    citation = Citation(
        root_id=memory.project_root_id or memory.thread_id or "memory",
        path=f"memory://{memory.id}",
        citation_type="memory",
        citation_id=citation_id,
        memory_id=memory.id,
        stale=memory.status == "stale" or is_expired(memory.expires_at),
        query=None,
    )
    return ContextItem(
        id=make_context_id("memory", memory.id, citation_id),
        kind="memory",
        text=memory.text,
        metadata={
            "source": "memory",
            "memory_id": memory.id,
            "scope": memory.scope,
            "type": memory.type,
            "score": result.score,
            "score_reasons": [reason.model_dump() for reason in result.score_reasons],
            "duplicate_ids": result.duplicate_ids,
        },
        trust="runtime_generated",
        budget_cost=estimate_budget_cost(memory.text),
        citations=[citation],
    )


def is_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    try:
        return datetime.fromisoformat(expires_at.replace("Z", "+00:00")) < datetime.now(timezone.utc)
    except ValueError:
        return False


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_value(child) for key, child in value.items() if key.lower() not in {"api_key", "apikey", "authorization", "cookie"}}
    if isinstance(value, list):
        return [redact_value(child) for child in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def _record_from_row(row) -> MemoryRecord:
    return MemoryRecord(
        id=row["id"],
        scope=row["scope"],
        type=row["type"],
        status=row["status"],
        text=row["text"],
        tags=_loads(row["tags_json"]) or [],
        confidence=float(row["confidence"]),
        source=MemorySource.model_validate(_loads(row["source_json"]) or {}),
        project_root_id=row["project_root_id"],
        thread_id=row["thread_id"],
        merged_ids=_loads(row["merged_ids_json"]) or [],
        last_used_at=row["last_used_at"],
        expires_at=row["expires_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _record_params(record: MemoryRecord) -> tuple[Any, ...]:
    return (
        record.id,
        record.scope,
        record.type,
        record.status,
        record.text,
        _json(record.tags),
        record.confidence,
        _json(record.source.model_dump()),
        record.project_root_id,
        record.thread_id,
        _json(record.merged_ids),
        record.last_used_at,
        record.expires_at,
        record.created_at,
        record.updated_at,
    )


def _candidate_from_row(row) -> MemoryCandidate:
    return MemoryCandidate(
        id=row["id"],
        thread_id=row["thread_id"],
        status=row["status"],
        suggested_scope=row["suggested_scope"],
        suggested_type=row["suggested_type"],
        text=row["text"],
        confidence=float(row["confidence"]),
        reason=row["reason"],
        risk=row["risk"],
        guard=GuardResult.model_validate(_loads(row["guard_json"]) or {}),
        duplicate_ids=_loads(row["duplicate_ids_json"]) or [],
        source=MemorySource.model_validate(_loads(row["source_json"]) or {}),
        created_memory_id=row["created_memory_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _redacted_source(source: MemorySource) -> MemorySource:
    safe = redact_value(source.model_dump())
    return MemorySource.model_validate(safe)


def _guard_text(*parts: Any) -> str:
    return "\n".join(json.dumps(redact_value(part), ensure_ascii=False, sort_keys=True) if not isinstance(part, str) else part for part in parts if part is not None)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


def _normalize_tags(tags: list[str]) -> list[str]:
    return sorted({tag.strip().lower() for tag in tags if tag.strip()})[:20]


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", (text or "").lower())


def _normalize(text: str) -> str:
    return " ".join(_terms(text))


def _dedupe_results(results: list[MemoryRetrievalResult]) -> tuple[list[MemoryRetrievalResult], dict[str, list[str]]]:
    by_text: dict[str, MemoryRetrievalResult] = {}
    duplicates: dict[str, list[str]] = {}
    for result in results:
        key = _normalize(result.memory.text)
        existing = by_text.get(key)
        if existing is None or result.score > existing.score:
            if existing is not None:
                duplicates.setdefault(result.memory.id, []).append(existing.memory.id)
            by_text[key] = result
        else:
            duplicates.setdefault(existing.memory.id, []).append(result.memory.id)
    return list(by_text.values()), duplicates


def _candidate_text(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) > 500:
        cleaned = cleaned[:500]
    return cleaned


def _candidate_type(text: str) -> MemoryType:
    lowered = text.lower()
    if "prefer" in lowered or "preference" in lowered:
        return "preference"
    if "decided" in lowered or "decision" in lowered:
        return "decision"
    if "workflow" in lowered:
        return "workflow"
    if "feedback" in lowered:
        return "feedback"
    return "fact"
