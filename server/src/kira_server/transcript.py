from __future__ import annotations

import hashlib
import json
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from kira_server.context import Citation, ContextItem, estimate_budget_cost, make_context_id
from kira_server.providers.config import redact_text
from kira_server.storage.database import RuntimeStorage, utc_now

ConversationStatus = Literal["active", "archived"]
TranscriptRole = Literal["user", "assistant", "tool", "system"]
TranscriptStatus = Literal["draft", "streaming", "completed", "error", "cancelled"]
TranscriptPartKind = Literal["text", "tool_summary", "tool_replacement", "compaction", "interrupt", "resume", "error", "done", "metadata", "fork", "rollback"]
BranchOperation = Literal["fork", "rollback"]
CompactionStatus = Literal["active", "stale", "error"]
ReplacementStatus = Literal["active", "invalidated"]
ReplacementReason = Literal["too_large", "secret_guard", "manual_clear", "compaction_prune"]
RetentionPolicy = Literal["none", "debug_only", "local_blob"]
SummarizerMode = Literal["fixture", "real"]

MAX_PART_TEXT = 4_000
MAX_CONTEXT_MESSAGES = 8
MAX_SUMMARY_TEXT = 2_400
DEFAULT_COMPACTION_TAIL_MESSAGES = 4
TOOL_REPLACEMENT_CHAR_THRESHOLD = 2_000


class Conversation(BaseModel):
    id: str
    title: str | None = None
    status: ConversationStatus = "active"
    archived: bool = False
    active_head_message_id: str | None = None
    forked_from_conversation_id: str | None = None
    forked_from_message_id: str | None = None
    forked_from_turn_id: str | None = None
    created_at: str
    updated_at: str


class TranscriptPart(BaseModel):
    id: str
    message_id: str
    conversation_id: str
    turn_id: str | None = None
    thread_id: str | None = None
    kind: TranscriptPartKind
    seq: int
    text: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    visible: bool = True
    token_estimate: int = 0
    created_at: str


class TranscriptMessage(BaseModel):
    id: str
    conversation_id: str
    turn_id: str | None = None
    thread_id: str | None = None
    parent_message_id: str | None = None
    logical_parent_message_id: str | None = None
    role: TranscriptRole
    status: TranscriptStatus
    branch_status: str = "active"
    parts: list[TranscriptPart] = Field(default_factory=list)
    created_at: str
    updated_at: str


class ConversationTurn(BaseModel):
    turn_id: str
    conversation_id: str
    thread_id: str | None = None
    user_message_id: str | None = None
    assistant_message_id: str | None = None
    status: TranscriptStatus = "draft"
    prompt: str
    created_at: str
    updated_at: str


class CompactionSummary(BaseModel):
    id: str
    conversation_id: str
    source_first_message_id: str | None = None
    source_last_message_id: str | None = None
    source_message_ids: list[str] = Field(default_factory=list)
    source_turn_ids: list[str] = Field(default_factory=list)
    replacement_ids: list[str] = Field(default_factory=list)
    source_hash: str
    tail_start_message_id: str | None = None
    summary: str
    source_token_estimate: int = 0
    summary_token_estimate: int = 0
    summarizer: dict[str, Any] = Field(default_factory=dict)
    status: CompactionStatus = "active"
    stale: bool = False
    stale_reason: str | None = None
    previous_summary_id: str | None = None
    trigger: str = "manual"
    created_at: str
    updated_at: str


class ToolOutputReplacement(BaseModel):
    id: str
    conversation_id: str
    turn_id: str | None = None
    thread_id: str | None = None
    message_id: str
    part_id: str | None = None
    tool_name: str
    output_hash: str
    summary: str
    omitted_char_count: int = 0
    reason: ReplacementReason
    retention_policy: RetentionPolicy = "none"
    status: ReplacementStatus = "active"
    redacted_reference: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ConversationBranchRecord(BaseModel):
    id: str
    operation: BranchOperation
    source_conversation_id: str
    target_conversation_id: str
    source_message_id: str | None = None
    source_turn_id: str | None = None
    previous_active_head_id: str | None = None
    new_active_head_id: str | None = None
    reason: dict[str, Any] = Field(default_factory=dict)
    status: str = "applied"
    created_at: str
    updated_at: str


class ActiveHeadTransition(BaseModel):
    id: str
    conversation_id: str
    operation: BranchOperation
    previous_active_head_id: str | None = None
    new_active_head_id: str | None = None
    branch_record_id: str | None = None
    reason: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ConversationCreateRequest(BaseModel):
    title: str | None = None


class ConversationUpdateRequest(BaseModel):
    title: str | None = None
    archived: bool | None = None


class ForkConversationRequest(BaseModel):
    source_message_id: str | None = None
    source_turn_id: str | None = None
    title: str | None = None
    reason: str | None = None


class RollbackConversationRequest(BaseModel):
    target_message_id: str | None = None
    target_turn_id: str | None = None
    reason: str | None = None


class BranchOperationResponse(BaseModel):
    conversation: Conversation
    branch_record: ConversationBranchRecord
    active_head_transition: ActiveHeadTransition
    active_head_message_id: str | None = None
    inactive_message_ids: list[str] = Field(default_factory=list)


class TranscriptOverflowThresholds(BaseModel):
    max_raw_messages: int = Field(default=12, ge=1, le=1_000)
    max_estimated_tokens: int = Field(default=4_000, ge=100, le=200_000)
    max_estimated_chars: int = Field(default=16_000, ge=500, le=1_000_000)
    budget_pressure_ratio: float = Field(default=0.8, ge=0.1, le=1.0)


class CompactConversationRequest(BaseModel):
    summarizer_mode: Literal["fixture", "real", "auto"] = "fixture"
    provider: str | None = None
    model: str | None = None
    tail_messages: int = Field(default=DEFAULT_COMPACTION_TAIL_MESSAGES, ge=0, le=50)
    max_source_messages: int | None = Field(default=None, ge=1, le=1_000)
    refresh: bool = False
    trigger: Literal["manual", "overflow", "refresh"] = "manual"
    thresholds: TranscriptOverflowThresholds | None = None


class CompactConversationResponse(BaseModel):
    conversation_id: str
    summary: CompactionSummary
    context_item: ContextItem
    replaced_raw_messages: int
    tail_start_message_id: str | None = None
    status: str = "compacted"
    omitted: list[dict[str, Any]] = Field(default_factory=list)


class PreparedTurn(BaseModel):
    conversation: Conversation
    turn: ConversationTurn
    user_message: TranscriptMessage
    assistant_message: TranscriptMessage
    previous_head_message_id: str | None = None


class TranscriptContextResult(BaseModel):
    items: list[ContextItem]
    trace: dict[str, Any]


class TranscriptService:
    def __init__(self, storage: RuntimeStorage) -> None:
        self.storage = storage

    def create_conversation(self, request: ConversationCreateRequest | None = None) -> Conversation:
        now = utc_now()
        conversation = Conversation(
            id=f"conv_{uuid4().hex}",
            title=redact_text((request.title if request else None) or "New conversation"),
            status="active",
            archived=False,
            created_at=now,
            updated_at=now,
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations(
                  id, title, status, archived, active_head_message_id,
                  forked_from_conversation_id, forked_from_message_id, forked_from_turn_id,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation.id,
                    conversation.title,
                    conversation.status,
                    int(conversation.archived),
                    conversation.active_head_message_id,
                    conversation.forked_from_conversation_id,
                    conversation.forked_from_message_id,
                    conversation.forked_from_turn_id,
                    now,
                    now,
                ),
            )
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self.storage.database.connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        return _conversation_from_row(row) if row else None

    def list_conversations(self, *, include_archived: bool = False) -> list[Conversation]:
        with self.storage.database.connect() as conn:
            if include_archived:
                rows = conn.execute("SELECT * FROM conversations ORDER BY updated_at DESC").fetchall()
            else:
                rows = conn.execute("SELECT * FROM conversations WHERE archived = 0 ORDER BY updated_at DESC").fetchall()
        return [_conversation_from_row(row) for row in rows]

    def update_conversation(self, conversation_id: str, request: ConversationUpdateRequest) -> Conversation | None:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            return None
        archived = conversation.archived if request.archived is None else request.archived
        status: ConversationStatus = "archived" if archived else "active"
        title = redact_text(request.title) if request.title is not None else conversation.title
        with self.storage.database.connect() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, status = ?, archived = ?, updated_at = ? WHERE id = ?",
                (title, status, int(archived), utc_now(), conversation_id),
            )
        return self.get_conversation(conversation_id)

    def fork_conversation(self, conversation_id: str, request: ForkConversationRequest) -> BranchOperationResponse:
        source = self.get_conversation(conversation_id)
        if source is None:
            raise ValueError("conversation_not_found")
        if source.archived:
            raise ValueError("conversation_archived")
        target_message = self._resolve_branch_target(
            conversation_id,
            message_id=request.source_message_id,
            turn_id=request.source_turn_id,
            target_label="source",
        )
        now = utc_now()
        fork = Conversation(
            id=f"conv_{uuid4().hex}",
            title=redact_text(request.title or f"Fork: {source.title or 'Conversation'}"),
            status="active",
            archived=False,
            active_head_message_id=target_message.id,
            forked_from_conversation_id=source.id,
            forked_from_message_id=target_message.id,
            forked_from_turn_id=target_message.turn_id,
            created_at=now,
            updated_at=now,
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations(
                  id, title, status, archived, active_head_message_id,
                  forked_from_conversation_id, forked_from_message_id, forked_from_turn_id,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fork.id,
                    fork.title,
                    fork.status,
                    int(fork.archived),
                    fork.active_head_message_id,
                    fork.forked_from_conversation_id,
                    fork.forked_from_message_id,
                    fork.forked_from_turn_id,
                    now,
                    now,
                ),
            )
        record, transition = self._record_branch_operation(
            operation="fork",
            source_conversation_id=source.id,
            target_conversation_id=fork.id,
            source_message_id=target_message.id,
            source_turn_id=target_message.turn_id,
            previous_active_head_id=None,
            new_active_head_id=target_message.id,
            reason={"text": redact_text(request.reason), "source_active_head_id": source.active_head_message_id},
        )
        return BranchOperationResponse(
            conversation=fork,
            branch_record=record,
            active_head_transition=transition,
            active_head_message_id=fork.active_head_message_id,
        )

    def rollback_conversation(self, conversation_id: str, request: RollbackConversationRequest) -> BranchOperationResponse:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise ValueError("conversation_not_found")
        if conversation.archived:
            raise ValueError("conversation_archived")
        target_message = self._resolve_branch_target(
            conversation_id,
            message_id=request.target_message_id,
            turn_id=request.target_turn_id,
            target_label="target",
        )
        previous_head = conversation.active_head_message_id
        now = utc_now()
        with self.storage.database.connect() as conn:
            conn.execute(
                "UPDATE conversations SET active_head_message_id = ?, updated_at = ? WHERE id = ?",
                (target_message.id, now, conversation_id),
            )
        inactive_message_ids = self._mark_inactive_branch_messages(conversation_id, target_message.id)
        record, transition = self._record_branch_operation(
            operation="rollback",
            source_conversation_id=conversation_id,
            target_conversation_id=conversation_id,
            source_message_id=target_message.id,
            source_turn_id=target_message.turn_id,
            previous_active_head_id=previous_head,
            new_active_head_id=target_message.id,
            reason={"text": redact_text(request.reason)},
        )
        return BranchOperationResponse(
            conversation=self.get_conversation(conversation_id) or conversation,
            branch_record=record,
            active_head_transition=transition,
            active_head_message_id=target_message.id,
            inactive_message_ids=inactive_message_ids,
        )

    def prepare_turn(self, *, prompt: str, thread_id: str, conversation_id: str | None = None) -> PreparedTurn:
        conversation = self.get_conversation(conversation_id) if conversation_id else self.create_conversation(ConversationCreateRequest(title=_default_title(prompt)))
        if conversation is None or conversation.archived:
            raise ValueError("conversation_not_found_or_archived")
        previous_head = conversation.active_head_message_id
        turn_id = f"turn_{uuid4().hex}"
        now = utc_now()
        user = self._create_message(
            conversation_id=conversation.id,
            turn_id=turn_id,
            thread_id=thread_id,
            role="user",
            status="completed",
            parent_message_id=previous_head,
            text=prompt,
            part_kind="text",
            visible=True,
        )
        assistant = self._create_message(
            conversation_id=conversation.id,
            turn_id=turn_id,
            thread_id=thread_id,
            role="assistant",
            status="streaming",
            parent_message_id=user.id,
            text="",
            part_kind="text",
            visible=True,
        )
        turn = ConversationTurn(
            turn_id=turn_id,
            conversation_id=conversation.id,
            thread_id=thread_id,
            user_message_id=user.id,
            assistant_message_id=assistant.id,
            status="streaming",
            prompt=redact_text(prompt),
            created_at=now,
            updated_at=now,
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_turns(turn_id, conversation_id, thread_id, user_message_id, assistant_message_id, status, prompt, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (turn.turn_id, turn.conversation_id, turn.thread_id, turn.user_message_id, turn.assistant_message_id, turn.status, turn.prompt, now, now),
            )
            conn.execute(
                "INSERT INTO conversation_run_links(conversation_id, turn_id, thread_id, created_at) VALUES (?, ?, ?, ?)",
                (turn.conversation_id, turn.turn_id, thread_id, now),
            )
            conn.execute(
                "UPDATE conversations SET active_head_message_id = ?, updated_at = ? WHERE id = ?",
                (user.id, now, conversation.id),
            )
        return PreparedTurn(conversation=self.get_conversation(conversation.id) or conversation, turn=turn, user_message=user, assistant_message=assistant, previous_head_message_id=previous_head)

    def transcript(self, conversation_id: str) -> list[TranscriptMessage]:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            return []
        active_chain = self._active_chain(conversation.active_head_message_id)
        active_ids = {message.id for message in active_chain}
        with self.storage.database.connect() as conn:
            rows = conn.execute("SELECT * FROM transcript_messages WHERE conversation_id = ? ORDER BY created_at, id", (conversation_id,)).fetchall()
            local_ids = {row["id"] for row in rows}
            inherited = [message for message in active_chain if message.id not in local_ids]
            part_ids = list(local_ids | {message.id for message in inherited})
            parts = []
            for message_id in part_ids:
                parts.extend(conn.execute("SELECT * FROM transcript_parts WHERE message_id = ? ORDER BY seq", (message_id,)).fetchall())
        by_message: dict[str, list[TranscriptPart]] = {}
        for part in parts:
            by_message.setdefault(part["message_id"], []).append(_part_from_row(part))
        messages = inherited + [_message_from_row(row, by_message.get(row["id"], [])) for row in rows]
        deduped: dict[str, TranscriptMessage] = {}
        for message in messages:
            status = "inherited" if message.conversation_id != conversation_id else ("active" if message.id in active_ids else "inactive")
            deduped[message.id] = message.model_copy(update={"branch_status": status, "parts": by_message.get(message.id, message.parts)})
        return sorted(deduped.values(), key=lambda message: (message.created_at, message.id))

    def list_compaction_summaries(self, conversation_id: str, *, include_stale: bool = True) -> list[CompactionSummary]:
        with self.storage.database.connect() as conn:
            if include_stale:
                rows = conn.execute(
                    "SELECT * FROM conversation_compaction_summaries WHERE conversation_id = ? ORDER BY created_at DESC",
                    (conversation_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM conversation_compaction_summaries WHERE conversation_id = ? AND status = 'active' ORDER BY created_at DESC",
                    (conversation_id,),
                ).fetchall()
        return [self._refresh_compaction_stale_status(_compaction_from_row(row)) for row in rows]

    def list_tool_output_replacements(
        self,
        *,
        conversation_id: str | None = None,
        thread_id: str | None = None,
        status: ReplacementStatus | None = None,
    ) -> list[ToolOutputReplacement]:
        clauses = []
        params: list[Any] = []
        if conversation_id:
            clauses.append("conversation_id = ?")
            params.append(conversation_id)
        if thread_id:
            clauses.append("thread_id = ?")
            params.append(thread_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.storage.database.connect() as conn:
            rows = conn.execute(f"SELECT * FROM tool_output_replacements {where} ORDER BY created_at DESC", params).fetchall()
        return [_replacement_from_row(row) for row in rows]

    def list_branch_records(self, conversation_id: str) -> list[ConversationBranchRecord]:
        with self.storage.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM conversation_branch_records
                WHERE source_conversation_id = ? OR target_conversation_id = ?
                ORDER BY created_at DESC
                """,
                (conversation_id, conversation_id),
            ).fetchall()
        return [_branch_record_from_row(row) for row in rows]

    def list_active_head_transitions(self, conversation_id: str) -> list[ActiveHeadTransition]:
        with self.storage.database.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversation_active_head_transitions WHERE conversation_id = ? ORDER BY created_at DESC",
                (conversation_id,),
            ).fetchall()
        return [_active_head_transition_from_row(row) for row in rows]

    def resume_conflict_for_thread(self, thread_id: str) -> dict[str, Any] | None:
        link = self._link_for_thread(thread_id)
        if not link:
            return None
        conversation = self.get_conversation(link["conversation_id"])
        if conversation is None:
            return None
        active_ids = {message.id for message in self._active_chain(conversation.active_head_message_id)}
        turn_message_ids = {value for value in (link.get("user_message_id"), link.get("assistant_message_id")) if value}
        if turn_message_ids & active_ids:
            return None
        return {
            "code": "inactive_branch_conflict",
            "conversation_id": conversation.id,
            "thread_id": thread_id,
            "turn_id": link.get("turn_id"),
            "active_head_message_id": conversation.active_head_message_id,
            "turn_message_ids": sorted(turn_message_ids),
        }

    def compact_conversation(
        self,
        conversation_id: str,
        request: CompactConversationRequest | None = None,
        *,
        summarizer_metadata: dict[str, Any] | None = None,
        summary_text: str | None = None,
    ) -> CompactConversationResponse:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise ValueError("conversation_not_found")
        if conversation.archived:
            raise ValueError("conversation_archived")
        payload = request or CompactConversationRequest()
        chain = self._active_chain(conversation.active_head_message_id)
        candidates = [message for message in chain if message.role in {"user", "assistant"} and message.status in {"completed", "streaming"}]
        if not candidates:
            raise ValueError("conversation_empty")
        source_messages, tail_start_message_id = _compaction_source_and_tail(candidates, payload.tail_messages, payload.max_source_messages)
        if not source_messages:
            raise ValueError("conversation_empty")
        replacements = self._replacements_for_source(source_messages)
        previous = self._latest_compaction(conversation_id) if payload.refresh or payload.trigger == "refresh" else None
        source_hash = _source_hash(source_messages, replacements)
        source_text = _source_text(source_messages, replacements)
        resolved_summary_text = _bounded_summary(summary_text) if summary_text else _fixture_summary(source_messages, replacements)
        now = utc_now()
        summary = CompactionSummary(
            id=f"cmp_{uuid4().hex}",
            conversation_id=conversation_id,
            source_first_message_id=source_messages[0].id,
            source_last_message_id=source_messages[-1].id,
            source_message_ids=[message.id for message in source_messages],
            source_turn_ids=_unique([message.turn_id for message in source_messages if message.turn_id]),
            replacement_ids=[replacement.id for replacement in replacements],
            source_hash=source_hash,
            tail_start_message_id=tail_start_message_id,
            summary=resolved_summary_text,
            source_token_estimate=estimate_budget_cost(source_text),
            summary_token_estimate=estimate_budget_cost(resolved_summary_text),
            summarizer=_summarizer_metadata(payload, summarizer_metadata),
            status="active",
            stale=False,
            stale_reason=None,
            previous_summary_id=previous.id if previous else None,
            trigger=payload.trigger,
            created_at=now,
            updated_at=now,
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_compaction_summaries(
                  id, conversation_id, source_first_message_id, source_last_message_id,
                  source_message_ids_json, source_turn_ids_json, replacement_ids_json,
                  source_hash, tail_start_message_id, summary, source_token_estimate,
                  summary_token_estimate, summarizer_json, status, stale_reason,
                  previous_summary_id, trigger, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.id,
                    summary.conversation_id,
                    summary.source_first_message_id,
                    summary.source_last_message_id,
                    _json(summary.source_message_ids),
                    _json(summary.source_turn_ids),
                    _json(summary.replacement_ids),
                    summary.source_hash,
                    summary.tail_start_message_id,
                    summary.summary,
                    summary.source_token_estimate,
                    summary.summary_token_estimate,
                    _json(summary.summarizer),
                    summary.status,
                    summary.stale_reason,
                    summary.previous_summary_id,
                    summary.trigger,
                    now,
                    now,
                ),
            )
        if previous and previous.status == "active":
            self._mark_compaction_stale(previous.id, "refreshed_by_new_summary")
        artifact = self._create_message(
            conversation_id=conversation_id,
            role="system",
            status="completed",
            parent_message_id=conversation.active_head_message_id,
            text=summary.summary,
            part_kind="compaction",
            visible=False,
        )
        if artifact.parts:
            with self.storage.database.connect() as conn:
                conn.execute(
                    "UPDATE transcript_parts SET payload_json = ? WHERE id = ?",
                    (_json(_compaction_metadata(summary)), artifact.parts[0].id),
                )
        return CompactConversationResponse(
            conversation_id=conversation_id,
            summary=summary,
            context_item=_summary_context_item(summary),
            replaced_raw_messages=len(source_messages),
            tail_start_message_id=tail_start_message_id,
            omitted=[{"message_id": message.id, "reason": "covered_by_compaction_summary", "summary_id": summary.id} for message in source_messages],
        )

    def compact_for_overflow_if_needed(
        self,
        conversation_id: str,
        *,
        thresholds: TranscriptOverflowThresholds | None = None,
        context_budget_max_chars: int | None = None,
    ) -> dict[str, Any]:
        resolved = thresholds or TranscriptOverflowThresholds()
        conversation = self.get_conversation(conversation_id)
        if conversation is None or conversation.archived:
            return {"status": "skipped", "reason": "conversation_not_found_or_archived"}
        chain = self._active_chain(conversation.active_head_message_id)
        messages = [message for message in chain if message.role in {"user", "assistant"} and message.status in {"completed", "streaming"}]
        if not _exceeds_overflow_thresholds(messages, resolved, context_budget_max_chars):
            return {"status": "skipped", "reason": "under_thresholds", "thresholds": resolved.model_dump()}
        usable, stale = self._latest_usable_compaction(conversation_id, chain)
        if usable is not None:
            return {"status": "skipped", "reason": "existing_summary", "summary_id": usable.id, "thresholds": resolved.model_dump()}
        try:
            response = self.compact_conversation(
                conversation_id,
                CompactConversationRequest(trigger="overflow", thresholds=resolved),
            )
        except Exception as exc:
            return {"status": "error", "reason": "overflow_compaction_failed", "message": redact_text(str(exc)), "thresholds": resolved.model_dump()}
        return {"status": "compacted", "summary_id": response.summary.id, "thresholds": resolved.model_dump(), "stale_omitted": [item.id for item in stale]}

    def context_for_conversation(self, conversation_id: str, *, thread_id: str | None = None, turn_id: str | None = None, limit: int = MAX_CONTEXT_MESSAGES) -> TranscriptContextResult:
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            return TranscriptContextResult(items=[], trace={"conversation_id": conversation_id, "reason": "not_found", "included": [], "omitted": []})
        chain = self._active_chain(conversation.active_head_message_id)
        selected = [message for message in chain if message.role in {"user", "assistant"} and message.status in {"completed", "streaming"}]
        items: list[ContextItem] = []
        included: list[dict[str, Any]] = []
        omitted: list[dict[str, Any]] = []
        usable_summary, stale_summaries = self._latest_usable_compaction(conversation_id, chain)
        for summary in stale_summaries:
            omitted.append({"summary_id": summary.id, "kind": "compaction_summary", "reason": "stale", "stale_reason": summary.stale_reason})
        covered_message_ids: set[str] = set()
        if usable_summary is not None:
            item = _summary_context_item(usable_summary)
            items.append(item)
            included.append(
                {
                    "summary_id": usable_summary.id,
                    "kind": "compaction_summary",
                    "source_message_ids": usable_summary.source_message_ids,
                    "tail_start_message_id": usable_summary.tail_start_message_id,
                    "budget_cost": item.budget_cost,
                    "decision": "included",
                }
            )
            covered_message_ids = set(usable_summary.source_message_ids)
            for message_id in usable_summary.source_message_ids:
                omitted.append({"message_id": message_id, "summary_id": usable_summary.id, "reason": "covered_by_compaction_summary"})
            selected = _tail_after_summary(selected, usable_summary)
        raw_omitted = selected[:-limit] if len(selected) > limit else []
        selected = selected[-limit:]
        for message in selected:
            if message.id in covered_message_ids:
                continue
            item = _message_context_item(conversation_id, message)
            if item is None:
                continue
            items.append(item)
            included.append({"message_id": message.id, "turn_id": message.turn_id, "role": message.role, "budget_cost": item.budget_cost, "decision": "included"})
        omitted.extend(
            {"message_id": message.id, "turn_id": message.turn_id, "role": message.role, "reason": "recent_limit"}
            for message in raw_omitted
            if message.id not in covered_message_ids
        )
        for item, decision in self._tool_context_items(conversation_id, chain, covered_message_ids):
            items.append(item)
            included.append(decision)
        active_ids = {message.id for message in chain}
        inactive_messages = self._inactive_messages(conversation_id, active_ids)
        omitted.extend(
            {
                "message_id": message.id,
                "turn_id": message.turn_id,
                "role": message.role,
                "reason": "inactive_branch",
            }
            for message in inactive_messages
        )
        branch_records = self.list_branch_records(conversation_id)
        trace = {
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "active_head_message_id": conversation.active_head_message_id,
            "branch": {
                "forked_from_conversation_id": conversation.forked_from_conversation_id,
                "forked_from_message_id": conversation.forked_from_message_id,
                "forked_from_turn_id": conversation.forked_from_turn_id,
                "inactive_message_count": len(inactive_messages),
                "latest_record": (branch_records[0].model_dump() if branch_records else None),
            },
            "included": included,
            "omitted": omitted,
            "summaries": [
                summary.model_dump()
                for summary in ([usable_summary] if usable_summary else [])
                + stale_summaries
            ],
        }
        if thread_id:
            with self.storage.database.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO transcript_context_traces(thread_id, conversation_id, turn_id, trace_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(thread_id) DO UPDATE SET trace_json=excluded.trace_json, updated_at=excluded.updated_at
                    """,
                    (thread_id, conversation_id, turn_id, _json(trace), utc_now(), utc_now()),
                )
        return TranscriptContextResult(items=items, trace=trace)

    def append_event(self, thread_id: str, event_type: str, data: dict[str, Any]) -> None:
        link = self._link_for_thread(thread_id)
        if not link:
            return
        assistant_id = link.get("assistant_message_id")
        if not assistant_id:
            return
        if event_type == "text_delta":
            text = _event_text(data)
            if text:
                self._append_part(assistant_id, kind="text", text=text, payload={}, visible=True)
            elif data.get("kind"):
                self._append_tool_event(assistant_id, data)
            return
        if event_type == "thinking_delta":
            return
        if event_type in {"tool_result", "tool_start", "side_effect_reused"}:
            self._append_tool_event(assistant_id, data)
            return
        if event_type == "interrupt":
            self._append_part(assistant_id, kind="interrupt", text=_bounded(str(data.get("title") or data.get("kind") or "Human input required")), payload=data, visible=False)
            self._set_turn_status(thread_id, "streaming", message_status="streaming")
            return
        if event_type == "resume":
            self._append_part(assistant_id, kind="resume", text=f"Decision: {redact_text(str(data.get('decision') or 'submitted'))}", payload=data, visible=False)
            return
        if event_type == "error":
            self._append_part(assistant_id, kind="error", text=_bounded(str(data.get("message") or data.get("code") or "Run failed")), payload=data, visible=False)
            self._set_turn_status(thread_id, "error", message_status="error")
            return
        if event_type == "done":
            self._append_part(assistant_id, kind="done", text=_bounded(str(data.get("message") or "Run completed")), payload=data, visible=False)
            self._set_turn_status(thread_id, "completed", message_status="completed", active_head_message_id=assistant_id)

    def mark_cancelled(self, thread_id: str) -> None:
        link = self._link_for_thread(thread_id)
        if not link:
            return
        assistant_id = link.get("assistant_message_id")
        if assistant_id:
            self._append_part(assistant_id, kind="error", text="Run cancelled", payload={"code": "cancelled"}, visible=False)
        self._set_turn_status(thread_id, "cancelled", message_status="cancelled")

    def _append_tool_event(self, assistant_id: str, data: dict[str, Any]) -> None:
        tool_payload = _tool_output_payload(data)
        raw_text = _stable_json(tool_payload)
        reason = _replacement_reason(tool_payload, raw_text)
        if reason is None:
            self._append_part(assistant_id, kind="tool_summary", text=_summary_text(data), payload=data, visible=False)
            return
        stub = _replacement_stub(tool_payload, raw_text, reason)
        part = self._append_part(
            assistant_id,
            kind="tool_replacement",
            text=stub["summary"],
            payload={"replacement": stub},
            visible=False,
        )
        replacement = self._insert_tool_output_replacement(part, tool_payload, raw_text, reason, stub["summary"])
        with self.storage.database.connect() as conn:
            conn.execute(
                "UPDATE transcript_parts SET payload_json = ? WHERE id = ?",
                (_json({"replacement": _replacement_metadata(replacement)}), part.id),
            )
        self._stale_summaries_referencing_replacement(replacement)

    def _insert_tool_output_replacement(
        self,
        part: TranscriptPart,
        data: dict[str, Any],
        raw_text: str,
        reason: ReplacementReason,
        summary: str,
    ) -> ToolOutputReplacement:
        now = utc_now()
        output_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        replacement = ToolOutputReplacement(
            id=f"repl_{uuid4().hex}",
            conversation_id=part.conversation_id,
            turn_id=part.turn_id,
            thread_id=part.thread_id,
            message_id=part.message_id,
            part_id=part.id,
            tool_name=str(data.get("name") or data.get("tool") or data.get("kind") or "tool"),
            output_hash=output_hash,
            summary=summary,
            omitted_char_count=max(0, len(raw_text) - len(summary)),
            reason=reason,
            retention_policy="none" if reason == "secret_guard" else "debug_only",
            status="active",
            redacted_reference={
                "replacement_id": None,
                "source_part_id": part.id,
                "output_hash_prefix": output_hash[:16],
                "raw_blob": "not_exposed_stage_08b",
            },
            created_at=now,
            updated_at=now,
        )
        replacement.redacted_reference["replacement_id"] = replacement.id
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO tool_output_replacements(
                  id, conversation_id, turn_id, thread_id, message_id, part_id,
                  tool_name, output_hash, summary, omitted_char_count, reason,
                  retention_policy, status, redacted_reference_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    replacement.id,
                    replacement.conversation_id,
                    replacement.turn_id,
                    replacement.thread_id,
                    replacement.message_id,
                    replacement.part_id,
                    replacement.tool_name,
                    replacement.output_hash,
                    replacement.summary,
                    replacement.omitted_char_count,
                    replacement.reason,
                    replacement.retention_policy,
                    replacement.status,
                    _json(replacement.redacted_reference),
                    now,
                    now,
                ),
            )
        return replacement

    def _resolve_branch_target(
        self,
        conversation_id: str,
        *,
        message_id: str | None,
        turn_id: str | None,
        target_label: str,
    ) -> TranscriptMessage:
        if not message_id and not turn_id:
            raise ValueError(f"{target_label}_required")
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise ValueError("conversation_not_found")
        active_chain = self._active_chain(conversation.active_head_message_id)
        active_by_id = {message.id: message for message in active_chain}
        if turn_id and not message_id:
            with self.storage.database.connect() as conn:
                turn = conn.execute("SELECT * FROM conversation_turns WHERE turn_id = ?", (turn_id,)).fetchone()
            if turn is None:
                raise ValueError(f"{target_label}_turn_not_found")
            message_id = turn["assistant_message_id"] or turn["user_message_id"]
        if not message_id:
            raise ValueError(f"{target_label}_required")
        message = active_by_id.get(message_id)
        if message is None:
            with self.storage.database.connect() as conn:
                exists = conn.execute("SELECT id FROM transcript_messages WHERE id = ?", (message_id,)).fetchone()
            raise ValueError(f"{target_label}_inactive" if exists else f"{target_label}_message_not_found")
        return message

    def _mark_inactive_branch_messages(self, conversation_id: str, active_head_message_id: str | None) -> list[str]:
        active_ids = {message.id for message in self._active_chain(active_head_message_id)}
        inactive_ids: list[str] = []
        with self.storage.database.connect() as conn:
            rows = conn.execute(
                "SELECT id FROM transcript_messages WHERE conversation_id = ? ORDER BY created_at, id",
                (conversation_id,),
            ).fetchall()
            inactive_ids = [row["id"] for row in rows if row["id"] not in active_ids]
            if inactive_ids:
                placeholders = ",".join("?" for _ in inactive_ids)
                conn.execute(
                    f"UPDATE transcript_messages SET branch_status = 'inactive', updated_at = ? WHERE id IN ({placeholders})",
                    [utc_now(), *inactive_ids],
                )
            if active_ids:
                placeholders = ",".join("?" for _ in active_ids)
                conn.execute(
                    f"UPDATE transcript_messages SET branch_status = 'active', updated_at = ? WHERE conversation_id = ? AND id IN ({placeholders})",
                    [utc_now(), conversation_id, *active_ids],
                )
        return inactive_ids

    def _inactive_messages(self, conversation_id: str, active_ids: set[str]) -> list[TranscriptMessage]:
        with self.storage.database.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM transcript_messages WHERE conversation_id = ? ORDER BY created_at, id",
                (conversation_id,),
            ).fetchall()
        return [_message_from_row(row, []) for row in rows if row["id"] not in active_ids]

    def _record_branch_operation(
        self,
        *,
        operation: BranchOperation,
        source_conversation_id: str,
        target_conversation_id: str,
        source_message_id: str | None,
        source_turn_id: str | None,
        previous_active_head_id: str | None,
        new_active_head_id: str | None,
        reason: dict[str, Any],
    ) -> tuple[ConversationBranchRecord, ActiveHeadTransition]:
        now = utc_now()
        record = ConversationBranchRecord(
            id=f"branch_{uuid4().hex}",
            operation=operation,
            source_conversation_id=source_conversation_id,
            target_conversation_id=target_conversation_id,
            source_message_id=source_message_id,
            source_turn_id=source_turn_id,
            previous_active_head_id=previous_active_head_id,
            new_active_head_id=new_active_head_id,
            reason=reason,
            status="applied",
            created_at=now,
            updated_at=now,
        )
        transition = ActiveHeadTransition(
            id=f"head_{uuid4().hex}",
            conversation_id=target_conversation_id,
            operation=operation,
            previous_active_head_id=previous_active_head_id,
            new_active_head_id=new_active_head_id,
            branch_record_id=record.id,
            reason=reason,
            created_at=now,
        )
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_branch_records(
                  id, operation, source_conversation_id, target_conversation_id,
                  source_message_id, source_turn_id, previous_active_head_id,
                  new_active_head_id, reason_json, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.operation,
                    record.source_conversation_id,
                    record.target_conversation_id,
                    record.source_message_id,
                    record.source_turn_id,
                    record.previous_active_head_id,
                    record.new_active_head_id,
                    _json(record.reason),
                    record.status,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO conversation_active_head_transitions(
                  id, conversation_id, operation, previous_active_head_id,
                  new_active_head_id, branch_record_id, reason_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition.id,
                    transition.conversation_id,
                    transition.operation,
                    transition.previous_active_head_id,
                    transition.new_active_head_id,
                    transition.branch_record_id,
                    _json(transition.reason),
                    now,
                ),
            )
        return record, transition

    def _latest_compaction(self, conversation_id: str) -> CompactionSummary | None:
        with self.storage.database.connect() as conn:
            row = conn.execute(
                "SELECT * FROM conversation_compaction_summaries WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 1",
                (conversation_id,),
            ).fetchone()
        return self._refresh_compaction_stale_status(_compaction_from_row(row)) if row else None

    def _latest_usable_compaction(self, conversation_id: str, chain: list[TranscriptMessage]) -> tuple[CompactionSummary | None, list[CompactionSummary]]:
        chain_ids = {message.id for message in chain}
        stale: list[CompactionSummary] = []
        for summary in self.list_compaction_summaries(conversation_id):
            if not set(summary.source_message_ids).issubset(chain_ids):
                stale.append(summary.model_copy(update={"stale": True, "stale_reason": summary.stale_reason or "outside_active_chain"}))
                continue
            if summary.status == "active" and not summary.stale:
                return summary, stale
            stale.append(summary)
        return None, stale

    def _refresh_compaction_stale_status(self, summary: CompactionSummary) -> CompactionSummary:
        if summary.status != "active":
            return summary.model_copy(update={"stale": True})
        source_messages = self._messages_by_ids(summary.source_message_ids)
        if len(source_messages) != len(summary.source_message_ids):
            return self._mark_compaction_stale(summary.id, "source_message_missing")
        replacements = self._replacements_by_ids(summary.replacement_ids)
        if len(replacements) != len(summary.replacement_ids):
            return self._mark_compaction_stale(summary.id, "replacement_missing")
        if _source_hash(source_messages, replacements) != summary.source_hash:
            return self._mark_compaction_stale(summary.id, "source_hash_changed")
        return summary

    def _mark_compaction_stale(self, summary_id: str, reason: str) -> CompactionSummary:
        now = utc_now()
        with self.storage.database.connect() as conn:
            conn.execute(
                "UPDATE conversation_compaction_summaries SET status = 'stale', stale_reason = ?, updated_at = ? WHERE id = ?",
                (reason, now, summary_id),
            )
            row = conn.execute("SELECT * FROM conversation_compaction_summaries WHERE id = ?", (summary_id,)).fetchone()
        return _compaction_from_row(row)

    def _messages_by_ids(self, message_ids: list[str]) -> list[TranscriptMessage]:
        if not message_ids:
            return []
        messages: list[TranscriptMessage] = []
        with self.storage.database.connect() as conn:
            for message_id in message_ids:
                row = conn.execute("SELECT * FROM transcript_messages WHERE id = ?", (message_id,)).fetchone()
                if row is None:
                    continue
                parts = conn.execute("SELECT * FROM transcript_parts WHERE message_id = ? ORDER BY seq", (message_id,)).fetchall()
                messages.append(_message_from_row(row, [_part_from_row(part) for part in parts]))
        return messages

    def _replacements_by_ids(self, replacement_ids: list[str]) -> list[ToolOutputReplacement]:
        if not replacement_ids:
            return []
        replacements: list[ToolOutputReplacement] = []
        with self.storage.database.connect() as conn:
            for replacement_id in replacement_ids:
                row = conn.execute("SELECT * FROM tool_output_replacements WHERE id = ?", (replacement_id,)).fetchone()
                if row is not None:
                    replacements.append(_replacement_from_row(row))
        return replacements

    def _replacements_for_source(self, messages: list[TranscriptMessage]) -> list[ToolOutputReplacement]:
        message_ids = {message.id for message in messages}
        conversation_id = messages[0].conversation_id if messages else None
        if not conversation_id:
            return []
        return [replacement for replacement in self.list_tool_output_replacements(conversation_id=conversation_id) if replacement.message_id in message_ids]

    def _stale_summaries_referencing_replacement(self, replacement: ToolOutputReplacement) -> None:
        with self.storage.database.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM conversation_compaction_summaries WHERE conversation_id = ? AND status = 'active'",
                (replacement.conversation_id,),
            ).fetchall()
        for summary in (_compaction_from_row(row) for row in rows):
            if replacement.id in summary.replacement_ids:
                self._mark_compaction_stale(summary.id, "replacement_changed")

    def _tool_context_items(
        self,
        conversation_id: str,
        chain: list[TranscriptMessage],
        covered_message_ids: set[str],
    ) -> list[tuple[ContextItem, dict[str, Any]]]:
        result: list[tuple[ContextItem, dict[str, Any]]] = []
        chain_ids = {message.id for message in chain}
        for message in chain:
            if message.id in covered_message_ids:
                continue
            for part in message.parts:
                if part.kind != "tool_summary" or not part.text.strip():
                    continue
                item = _tool_summary_context_item(conversation_id, message, part)
                result.append(
                    (
                        item,
                        {
                            "message_id": message.id,
                            "part_id": part.id,
                            "kind": "tool_summary",
                            "turn_id": message.turn_id,
                            "budget_cost": item.budget_cost,
                            "decision": "included",
                        },
                    )
                )
        with self.storage.database.connect() as conn:
            replacement_rows = conn.execute("SELECT * FROM tool_output_replacements WHERE status = 'active' ORDER BY created_at DESC").fetchall()
        for replacement in (_replacement_from_row(row) for row in replacement_rows):
            if replacement.message_id not in chain_ids or replacement.message_id in covered_message_ids:
                continue
            item = _replacement_context_item(replacement)
            result.append(
                (
                    item,
                    {
                        "replacement_id": replacement.id,
                        "message_id": replacement.message_id,
                        "part_id": replacement.part_id,
                        "kind": "tool_summary",
                        "reason": replacement.reason,
                        "omitted_char_count": replacement.omitted_char_count,
                        "budget_cost": item.budget_cost,
                        "decision": "included",
                    },
                )
            )
        return result

    def _create_message(
        self,
        *,
        conversation_id: str,
        role: TranscriptRole,
        status: TranscriptStatus,
        turn_id: str | None = None,
        thread_id: str | None = None,
        parent_message_id: str | None = None,
        logical_parent_message_id: str | None = None,
        text: str = "",
        part_kind: TranscriptPartKind = "text",
        visible: bool = True,
    ) -> TranscriptMessage:
        now = utc_now()
        message_id = f"msg_{uuid4().hex}"
        with self.storage.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO transcript_messages(id, conversation_id, turn_id, thread_id, parent_message_id, logical_parent_message_id, role, status, branch_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (message_id, conversation_id, turn_id, thread_id, parent_message_id, logical_parent_message_id, role, status, now, now),
            )
        message = TranscriptMessage(id=message_id, conversation_id=conversation_id, turn_id=turn_id, thread_id=thread_id, parent_message_id=parent_message_id, logical_parent_message_id=logical_parent_message_id, role=role, status=status, created_at=now, updated_at=now)
        if text:
            part = self._append_part(message_id, kind=part_kind, text=text, payload={}, visible=visible)
            message.parts.append(part)
        return message

    def _append_part(self, message_id: str, *, kind: TranscriptPartKind, text: str, payload: dict[str, Any] | None = None, visible: bool) -> TranscriptPart:
        with self.storage.database.connect() as conn:
            message = conn.execute("SELECT * FROM transcript_messages WHERE id = ?", (message_id,)).fetchone()
            if message is None:
                raise ValueError("message_not_found")
            seq_row = conn.execute("SELECT COALESCE(MAX(seq), 0) AS last_seq FROM transcript_parts WHERE message_id = ?", (message_id,)).fetchone()
            seq = int(seq_row["last_seq"]) + 1
            safe_text = _bounded(text)
            part = TranscriptPart(
                id=f"part_{uuid4().hex}",
                message_id=message_id,
                conversation_id=message["conversation_id"],
                turn_id=message["turn_id"],
                thread_id=message["thread_id"],
                kind=kind,
                seq=seq,
                text=safe_text,
                payload=_redact_value(payload or {}),
                visible=visible,
                token_estimate=estimate_budget_cost(safe_text),
                created_at=utc_now(),
            )
            conn.execute(
                """
                INSERT INTO transcript_parts(id, message_id, conversation_id, turn_id, thread_id, kind, seq, text, payload_json, visible, token_estimate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (part.id, part.message_id, part.conversation_id, part.turn_id, part.thread_id, part.kind, part.seq, part.text, _json(part.payload), int(part.visible), part.token_estimate, part.created_at),
            )
            conn.execute("UPDATE transcript_messages SET updated_at = ? WHERE id = ?", (utc_now(), message_id))
        return part

    def _set_turn_status(self, thread_id: str, status: TranscriptStatus, *, message_status: TranscriptStatus, active_head_message_id: str | None = None) -> None:
        with self.storage.database.connect() as conn:
            link = conn.execute("SELECT * FROM conversation_run_links WHERE thread_id = ?", (thread_id,)).fetchone()
            if link is None:
                return
            turn = conn.execute("SELECT * FROM conversation_turns WHERE turn_id = ?", (link["turn_id"],)).fetchone()
            if turn is None:
                return
            conn.execute("UPDATE conversation_turns SET status = ?, updated_at = ? WHERE turn_id = ?", (status, utc_now(), link["turn_id"]))
            if turn["assistant_message_id"]:
                conn.execute("UPDATE transcript_messages SET status = ?, updated_at = ? WHERE id = ?", (message_status, utc_now(), turn["assistant_message_id"]))
            if active_head_message_id:
                conn.execute("UPDATE conversations SET active_head_message_id = ?, updated_at = ? WHERE id = ?", (active_head_message_id, utc_now(), link["conversation_id"]))

    def _link_for_thread(self, thread_id: str) -> dict[str, Any] | None:
        with self.storage.database.connect() as conn:
            row = conn.execute(
                """
                SELECT l.conversation_id, l.turn_id, l.thread_id, t.user_message_id, t.assistant_message_id
                FROM conversation_run_links l
                LEFT JOIN conversation_turns t ON t.turn_id = l.turn_id
                WHERE l.thread_id = ?
                """,
                (thread_id,),
            ).fetchone()
        return dict(row) if row else None

    def _active_chain(self, head_message_id: str | None) -> list[TranscriptMessage]:
        if not head_message_id:
            return []
        chain: list[TranscriptMessage] = []
        seen: set[str] = set()
        current_id: str | None = head_message_id
        with self.storage.database.connect() as conn:
            while current_id and current_id not in seen:
                seen.add(current_id)
                row = conn.execute("SELECT * FROM transcript_messages WHERE id = ?", (current_id,)).fetchone()
                if row is None:
                    break
                parts = conn.execute("SELECT * FROM transcript_parts WHERE message_id = ? ORDER BY seq", (current_id,)).fetchall()
                chain.append(_message_from_row(row, [_part_from_row(part) for part in parts]))
                current_id = row["parent_message_id"]
        return list(reversed(chain))


def _conversation_from_row(row) -> Conversation:
    keys = row.keys()
    return Conversation(
        id=row["id"],
        title=row["title"],
        status=row["status"],
        archived=bool(row["archived"]),
        active_head_message_id=row["active_head_message_id"],
        forked_from_conversation_id=row["forked_from_conversation_id"] if "forked_from_conversation_id" in keys else None,
        forked_from_message_id=row["forked_from_message_id"] if "forked_from_message_id" in keys else None,
        forked_from_turn_id=row["forked_from_turn_id"] if "forked_from_turn_id" in keys else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _branch_record_from_row(row) -> ConversationBranchRecord:
    return ConversationBranchRecord(
        id=row["id"],
        operation=row["operation"],
        source_conversation_id=row["source_conversation_id"],
        target_conversation_id=row["target_conversation_id"],
        source_message_id=row["source_message_id"],
        source_turn_id=row["source_turn_id"],
        previous_active_head_id=row["previous_active_head_id"],
        new_active_head_id=row["new_active_head_id"],
        reason=_loads(row["reason_json"]) or {},
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _active_head_transition_from_row(row) -> ActiveHeadTransition:
    return ActiveHeadTransition(
        id=row["id"],
        conversation_id=row["conversation_id"],
        operation=row["operation"],
        previous_active_head_id=row["previous_active_head_id"],
        new_active_head_id=row["new_active_head_id"],
        branch_record_id=row["branch_record_id"],
        reason=_loads(row["reason_json"]) or {},
        created_at=row["created_at"],
    )


def _message_from_row(row, parts: list[TranscriptPart]) -> TranscriptMessage:
    return TranscriptMessage(
        id=row["id"],
        conversation_id=row["conversation_id"],
        turn_id=row["turn_id"],
        thread_id=row["thread_id"],
        parent_message_id=row["parent_message_id"],
        logical_parent_message_id=row["logical_parent_message_id"],
        role=row["role"],
        status=row["status"],
        branch_status=row["branch_status"],
        parts=parts,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _compaction_from_row(row) -> CompactionSummary:
    return CompactionSummary(
        id=row["id"],
        conversation_id=row["conversation_id"],
        source_first_message_id=row["source_first_message_id"],
        source_last_message_id=row["source_last_message_id"],
        source_message_ids=_loads(row["source_message_ids_json"]) or [],
        source_turn_ids=_loads(row["source_turn_ids_json"]) or [],
        replacement_ids=_loads(row["replacement_ids_json"]) or [],
        source_hash=row["source_hash"],
        tail_start_message_id=row["tail_start_message_id"],
        summary=row["summary"],
        source_token_estimate=int(row["source_token_estimate"] or 0),
        summary_token_estimate=int(row["summary_token_estimate"] or 0),
        summarizer=_loads(row["summarizer_json"]) or {},
        status=row["status"],
        stale=row["status"] == "stale",
        stale_reason=row["stale_reason"],
        previous_summary_id=row["previous_summary_id"],
        trigger=row["trigger"] or "manual",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _replacement_from_row(row) -> ToolOutputReplacement:
    return ToolOutputReplacement(
        id=row["id"],
        conversation_id=row["conversation_id"],
        turn_id=row["turn_id"],
        thread_id=row["thread_id"],
        message_id=row["message_id"],
        part_id=row["part_id"],
        tool_name=row["tool_name"],
        output_hash=row["output_hash"],
        summary=row["summary"],
        omitted_char_count=int(row["omitted_char_count"] or 0),
        reason=row["reason"],
        retention_policy=row["retention_policy"],
        status=row["status"],
        redacted_reference=_loads(row["redacted_reference_json"]) or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _part_from_row(row) -> TranscriptPart:
    return TranscriptPart(
        id=row["id"],
        message_id=row["message_id"],
        conversation_id=row["conversation_id"],
        turn_id=row["turn_id"],
        thread_id=row["thread_id"],
        kind=row["kind"],
        seq=int(row["seq"]),
        text=row["text"],
        payload=_loads(row["payload_json"]) or {},
        visible=bool(row["visible"]),
        token_estimate=int(row["token_estimate"]),
        created_at=row["created_at"],
    )


def _visible_text(message: TranscriptMessage) -> str:
    return "".join(part.text for part in message.parts if part.visible and part.kind == "text")


def _message_context_item(conversation_id: str, message: TranscriptMessage) -> ContextItem | None:
    text = _visible_text(message)
    if not text.strip():
        return None
    label = "User" if message.role == "user" else "Assistant"
    context_text = f"{label}: {text}"
    citation = Citation(
        root_id=conversation_id,
        path=f"conversation://{conversation_id}/{message.id}",
        citation_type="conversation",
        citation_id=message.id,
        stale=False,
    )
    return ContextItem(
        id=make_context_id("conversation", conversation_id, message.id),
        kind="conversation_history",
        text=context_text,
        metadata={
            "source": "conversation",
            "conversation_id": conversation_id,
            "turn_id": message.turn_id,
            "message_id": message.id,
            "role": message.role,
        },
        trust="user_supplied" if message.role == "user" else "runtime_generated",
        budget_cost=estimate_budget_cost(context_text),
        citations=[citation],
    )


def _summary_context_item(summary: CompactionSummary) -> ContextItem:
    citation = Citation(
        root_id=summary.conversation_id,
        path=f"conversation://{summary.conversation_id}/compaction/{summary.id}",
        citation_type="conversation_compaction",
        citation_id=summary.id,
        content_hash=summary.source_hash,
        stale=summary.stale or summary.status == "stale",
    )
    metadata = _compaction_metadata(summary)
    return ContextItem(
        id=make_context_id("compaction", summary.conversation_id, summary.id),
        kind="compaction_summary",
        text=f"Conversation summary:\n{summary.summary}",
        metadata=metadata,
        trust="runtime_generated",
        budget_cost=estimate_budget_cost(summary.summary, metadata),
        citations=[citation],
    )


def _tool_summary_context_item(conversation_id: str, message: TranscriptMessage, part: TranscriptPart) -> ContextItem:
    metadata = {
        "source": "conversation_tool_summary",
        "conversation_id": conversation_id,
        "turn_id": message.turn_id,
        "thread_id": message.thread_id,
        "message_id": message.id,
        "part_id": part.id,
        "kind": part.kind,
    }
    return ContextItem(
        id=make_context_id("tool-summary", conversation_id, part.id),
        kind="tool_summary",
        text=part.text,
        metadata=metadata,
        trust="runtime_generated",
        budget_cost=estimate_budget_cost(part.text, metadata),
        citations=[
            Citation(
                root_id=conversation_id,
                path=f"conversation://{conversation_id}/{message.id}#{part.id}",
                citation_type="conversation_tool_summary",
                citation_id=part.id,
                stale=False,
            )
        ],
    )


def _replacement_context_item(replacement: ToolOutputReplacement) -> ContextItem:
    metadata = _replacement_metadata(replacement)
    return ContextItem(
        id=make_context_id("replacement", replacement.conversation_id, replacement.id),
        kind="tool_summary",
        text=replacement.summary,
        payload={"replacement": metadata},
        metadata=metadata,
        trust="runtime_generated",
        budget_cost=estimate_budget_cost(replacement.summary, metadata),
        citations=[
            Citation(
                root_id=replacement.conversation_id,
                path=f"conversation://{replacement.conversation_id}/{replacement.message_id}#{replacement.part_id}",
                citation_type="tool_output_replacement",
                citation_id=replacement.id,
                content_hash=replacement.output_hash,
                stale=replacement.status != "active",
            )
        ],
    )


def _compaction_metadata(summary: CompactionSummary) -> dict[str, Any]:
    return {
        "source": "conversation_compaction",
        "conversation_id": summary.conversation_id,
        "summary_id": summary.id,
        "source_first_message_id": summary.source_first_message_id,
        "source_last_message_id": summary.source_last_message_id,
        "source_message_ids": summary.source_message_ids,
        "source_turn_ids": summary.source_turn_ids,
        "replacement_ids": summary.replacement_ids,
        "source_hash": summary.source_hash,
        "tail_start_message_id": summary.tail_start_message_id,
        "source_token_estimate": summary.source_token_estimate,
        "summary_token_estimate": summary.summary_token_estimate,
        "summarizer": summary.summarizer,
        "status": summary.status,
        "stale": summary.stale or summary.status == "stale",
        "stale_reason": summary.stale_reason,
        "previous_summary_id": summary.previous_summary_id,
        "trigger": summary.trigger,
    }


def _replacement_metadata(replacement: ToolOutputReplacement) -> dict[str, Any]:
    return {
        "source": "tool_output_replacement",
        "replacement_id": replacement.id,
        "conversation_id": replacement.conversation_id,
        "turn_id": replacement.turn_id,
        "thread_id": replacement.thread_id,
        "message_id": replacement.message_id,
        "part_id": replacement.part_id,
        "tool_name": replacement.tool_name,
        "output_hash": replacement.output_hash,
        "omitted_char_count": replacement.omitted_char_count,
        "reason": replacement.reason,
        "retention_policy": replacement.retention_policy,
        "status": replacement.status,
        "redacted_reference": replacement.redacted_reference,
    }


def _compaction_source_and_tail(
    messages: list[TranscriptMessage],
    tail_messages: int,
    max_source_messages: int | None,
) -> tuple[list[TranscriptMessage], str | None]:
    if tail_messages > 0 and len(messages) > tail_messages:
        source = messages[:-tail_messages]
        tail_start_message_id = messages[-tail_messages].id
    else:
        source = messages
        tail_start_message_id = None
    if max_source_messages is not None and len(source) > max_source_messages:
        source = source[-max_source_messages:]
    return source, tail_start_message_id


def _tail_after_summary(messages: list[TranscriptMessage], summary: CompactionSummary) -> list[TranscriptMessage]:
    if not summary.tail_start_message_id:
        return [message for message in messages if message.id not in set(summary.source_message_ids)]
    for index, message in enumerate(messages):
        if message.id == summary.tail_start_message_id:
            return messages[index:]
    return [message for message in messages if message.id not in set(summary.source_message_ids)]


def _source_hash(messages: list[TranscriptMessage], replacements: list[ToolOutputReplacement]) -> str:
    payload = {
        "messages": [
            {
                "id": message.id,
                "turn_id": message.turn_id,
                "thread_id": message.thread_id,
                "role": message.role,
                "status": message.status,
                "updated_at": message.updated_at,
                "parts": [
                    {
                        "id": part.id,
                        "kind": part.kind,
                        "text": part.text,
                        "visible": part.visible,
                        "token_estimate": part.token_estimate,
                    }
                    for part in message.parts
                ],
            }
            for message in messages
        ],
        "replacements": [
            {
                "id": replacement.id,
                "status": replacement.status,
                "output_hash": replacement.output_hash,
                "summary": replacement.summary,
                "retention_policy": replacement.retention_policy,
                "updated_at": replacement.updated_at,
            }
            for replacement in sorted(replacements, key=lambda item: item.id)
        ],
    }
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _source_text(messages: list[TranscriptMessage], replacements: list[ToolOutputReplacement]) -> str:
    blocks: list[str] = []
    for message in messages:
        visible = _visible_text(message)
        if visible.strip():
            blocks.append(f"{message.role}: {visible}")
        for part in message.parts:
            if part.kind == "tool_summary" and part.text.strip():
                blocks.append(f"tool_summary: {part.text}")
    for replacement in replacements:
        blocks.append(f"replacement {replacement.id}: {replacement.summary}")
    return redact_text("\n".join(blocks)) or ""


def _fixture_summary(messages: list[TranscriptMessage], replacements: list[ToolOutputReplacement]) -> str:
    user_goals: list[str] = []
    assistant_outcomes: list[str] = []
    decisions: list[str] = []
    open_questions: list[str] = []
    tool_outcomes: list[str] = []
    for message in messages:
        text = " ".join(_visible_text(message).split())
        if not text:
            continue
        snippet = _snippet(text, 220)
        if message.role == "user":
            user_goals.append(f"- {snippet} (source {message.id})")
        elif message.role == "assistant":
            assistant_outcomes.append(f"- {snippet} (source {message.id})")
        lower = text.lower()
        if any(token in lower for token in ("decided", "decision", "must", "should", "constraint", "approved", "rejected")):
            decisions.append(f"- {snippet} (source {message.id})")
        if text.rstrip().endswith("?"):
            open_questions.append(f"- {snippet} (source {message.id})")
        for part in message.parts:
            if part.kind == "tool_summary" and part.text.strip():
                tool_outcomes.append(f"- {_snippet(part.text, 180)} (part {part.id})")
    for replacement in replacements:
        tool_outcomes.append(
            f"- Replacement {replacement.id} for {replacement.tool_name}: {replacement.reason}, omitted {replacement.omitted_char_count} chars, hash {replacement.output_hash[:12]}"
        )
    sections = [
        ("User goals and constraints", user_goals),
        ("Assistant outcomes and decisions", assistant_outcomes),
        ("Explicit decisions or constraints", decisions),
        ("Open questions", open_questions),
        ("Bounded tool outcomes", tool_outcomes),
        ("Source references", [f"- {messages[0].id} through {messages[-1].id}; {len(messages)} messages covered"] if messages else []),
    ]
    lines: list[str] = []
    for title, entries in sections:
        if entries:
            lines.append(f"{title}:")
            lines.extend(entries[:8])
    summary = redact_text("\n".join(lines) or "No visible transcript content was available to summarize.") or ""
    return _bounded_summary(summary)


def _summarizer_metadata(payload: CompactConversationRequest, metadata: dict[str, Any] | None) -> dict[str, Any]:
    resolved_mode: SummarizerMode = "real" if payload.summarizer_mode == "real" and (metadata or {}).get("mode") == "real" else "fixture"
    base = {
        "mode": resolved_mode,
        "name": "fixture-transcript-summarizer" if resolved_mode == "fixture" else "openai-compatible-transcript-summarizer",
        "deterministic": resolved_mode == "fixture",
        "provider": metadata or {"mode": "fixture", "source": "default"},
    }
    if payload.summarizer_mode == "real" and resolved_mode == "fixture":
        base["fallback_reason"] = (metadata or {}).get("fallback_reason") or "real_provider_not_allowed_or_unavailable"
    return _redact_value(base)


def _exceeds_overflow_thresholds(
    messages: list[TranscriptMessage],
    thresholds: TranscriptOverflowThresholds,
    context_budget_max_chars: int | None,
) -> bool:
    raw_chars = sum(len(_visible_text(message)) + sum(len(part.text) for part in message.parts if part.kind == "tool_summary") for message in messages)
    estimated_tokens = estimate_budget_cost("".join(_visible_text(message) for message in messages))
    message_pressure = len(messages) > thresholds.max_raw_messages
    content_pressure = raw_chars > thresholds.max_estimated_chars or estimated_tokens > thresholds.max_estimated_tokens
    budget_pressure = False
    if context_budget_max_chars:
        budget_pressure = raw_chars >= int(context_budget_max_chars * thresholds.budget_pressure_ratio)
    return message_pressure and (content_pressure or budget_pressure)


def _replacement_reason(data: dict[str, Any], raw_text: str) -> ReplacementReason | None:
    if _contains_secret_like_value(data) or _contains_secret_like_text(raw_text):
        return "secret_guard"
    if len(raw_text) > TOOL_REPLACEMENT_CHAR_THRESHOLD:
        return "too_large"
    return None


def _tool_output_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if key not in {"provider", "skill", "timestamp"}
    }


def _replacement_stub(data: dict[str, Any], raw_text: str, reason: ReplacementReason) -> dict[str, Any]:
    tool_name = str(data.get("name") or data.get("tool") or data.get("kind") or "tool")
    output_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    summary = _bounded_summary(
        f"{tool_name} output replaced: reason={reason}; omitted_chars={max(0, len(raw_text) - 240)}; output_hash={output_hash[:16]}; "
        f"preview={_snippet(redact_text(raw_text) or '', 240)}"
    )
    return {
        "tool_name": tool_name,
        "summary": summary,
        "reason": reason,
        "omitted_char_count": max(0, len(raw_text) - len(summary)),
        "output_hash": output_hash,
        "retention_policy": "none" if reason == "secret_guard" else "debug_only",
        "raw_blob": "not_exposed_stage_08b",
    }


def _contains_secret_like_value(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"api_key", "apikey", "authorization", "cookie", "password", "secret", "token"}:
                return True
            if _contains_secret_like_value(child):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_secret_like_value(item) for item in value)
    if isinstance(value, str):
        return _contains_secret_like_text(value)
    return False


def _contains_secret_like_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("bearer ", "private_key", "-----begin private key-----", "api_key", "authorization")) or "sk-" in text


def _bounded_summary(text: str) -> str:
    safe = redact_text(text) or ""
    if len(safe) <= MAX_SUMMARY_TEXT:
        return safe
    return f"{safe[:MAX_SUMMARY_TEXT]}...[summary truncated {len(safe) - MAX_SUMMARY_TEXT} chars]"


def _snippet(text: str, limit: int) -> str:
    clean = " ".join((redact_text(text) or "").split())
    if len(clean) <= limit:
        return clean
    return f"{clean[:limit]}..."


def _unique(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _stable_json(value: Any) -> str:
    return json.dumps(_redact_value(value), ensure_ascii=False, sort_keys=True, default=str)


def _event_text(data: dict[str, Any]) -> str:
    text = data.get("text")
    return text if isinstance(text, str) else ""


def _summary_text(data: dict[str, Any]) -> str:
    name = data.get("name") or data.get("kind") or "tool"
    status = data.get("status") or "ok"
    preview = data.get("result") if "result" in data else data
    return _bounded(f"{name}: {status} {redact_text(json.dumps(_redact_value(preview), ensure_ascii=False, sort_keys=True))}")


def _bounded(text: str) -> str:
    redacted = redact_text(text or "")
    if len(redacted) <= MAX_PART_TEXT:
        return redacted
    return f"{redacted[:MAX_PART_TEXT]}...[truncated {len(redacted) - MAX_PART_TEXT} chars]"


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _redact_value(child)
            for key, child in value.items()
            if key.lower() not in {"api_key", "apikey", "has_api_key", "authorization", "cookie", "password", "secret", "token"}
        }
    if isinstance(value, list):
        return [_redact_value(child) for child in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def _default_title(prompt: str) -> str:
    title = " ".join(prompt.split())[:80]
    return title or "New conversation"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None
