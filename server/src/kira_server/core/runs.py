from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Literal
from uuid import uuid4


RunStatus = Literal["created", "running", "waiting_for_user", "completed", "error", "stopped"]


@dataclass(frozen=True)
class RunRecord:
    thread_id: str
    prompt: str
    fixture: str
    provider_mode: str
    provider_metadata: dict[str, Any]
    provider_selection: Any
    project_root: str | None = None
    skill_id: str | None = None
    workflow: Any | None = None
    skill_metadata: dict[str, Any] | None = None
    conversation_id: str | None = None
    turn_id: str | None = None
    user_message_id: str | None = None
    assistant_message_id: str | None = None
    context_items: list[dict[str, Any]] | None = None
    context_trace: dict[str, Any] | None = None
    status: RunStatus = "created"


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}

    def create(
        self,
        *,
        prompt: str,
        thread_id: str | None = None,
        fixture: str,
        provider_mode: str,
        provider_metadata: dict[str, Any],
        provider_selection: Any,
        project_root: str | None = None,
        skill_id: str | None = None,
        workflow: Any | None = None,
        skill_metadata: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        turn_id: str | None = None,
        user_message_id: str | None = None,
        assistant_message_id: str | None = None,
        context_items: list[dict[str, Any]] | None = None,
        context_trace: dict[str, Any] | None = None,
    ) -> RunRecord:
        record = RunRecord(
            thread_id=thread_id or f"local-{uuid4().hex}",
            prompt=prompt,
            fixture=fixture,
            provider_mode=provider_mode,
            provider_metadata=provider_metadata,
            provider_selection=provider_selection,
            project_root=project_root,
            skill_id=skill_id,
            workflow=workflow,
            skill_metadata=skill_metadata,
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            context_items=context_items,
            context_trace=context_trace,
        )
        self._runs[record.thread_id] = record
        return record

    def get(self, thread_id: str) -> RunRecord | None:
        return self._runs.get(thread_id)

    def set_status(self, thread_id: str, status: RunStatus) -> RunRecord | None:
        current = self._runs.get(thread_id)
        if current is None:
            return None

        updated = RunRecord(
            thread_id=current.thread_id,
            prompt=current.prompt,
            fixture=current.fixture,
            provider_mode=current.provider_mode,
            provider_metadata=current.provider_metadata,
            provider_selection=current.provider_selection,
            project_root=current.project_root,
            skill_id=current.skill_id,
            workflow=current.workflow,
            skill_metadata=current.skill_metadata,
            conversation_id=current.conversation_id,
            turn_id=current.turn_id,
            user_message_id=current.user_message_id,
            assistant_message_id=current.assistant_message_id,
            context_items=current.context_items,
            context_trace=current.context_trace,
            status=status,
        )
        self._runs[thread_id] = updated
        return updated

    def update_context(
        self,
        thread_id: str,
        *,
        context_items: list[dict[str, Any]],
        context_trace: dict[str, Any],
    ) -> RunRecord | None:
        current = self._runs.get(thread_id)
        if current is None:
            return None
        updated = RunRecord(
            thread_id=current.thread_id,
            prompt=current.prompt,
            fixture=current.fixture,
            provider_mode=current.provider_mode,
            provider_metadata=current.provider_metadata,
            provider_selection=current.provider_selection,
            project_root=current.project_root,
            skill_id=current.skill_id,
            workflow=current.workflow,
            skill_metadata=current.skill_metadata,
            conversation_id=current.conversation_id,
            turn_id=current.turn_id,
            user_message_id=current.user_message_id,
            assistant_message_id=current.assistant_message_id,
            context_items=context_items,
            context_trace=context_trace,
            status=current.status,
        )
        self._runs[thread_id] = updated
        return updated
