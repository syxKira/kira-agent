from __future__ import annotations

import json
import os
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from kira_server.context import ContextBudget, pack_context
from kira_server.core.events import KiraEvent
from kira_server.core.runs import InMemoryRunStore, RunStatus
from kira_server.graph_runtime.agent_loop import build_default_system_prompt, run_default_agent
from kira_server.graph_runtime.runtime import GraphRuntime, GraphRuntimeContext, failure_class_for_events
from kira_server.graph_runtime.hitl import ResumeRequest, ResumeResult, validate_resume_for_interrupt
from kira_server.memory import (
    ExtractionRequest,
    MemoryActionRequest,
    MemoryCreateRequest,
    MemoryScope,
    MemorySearchRequest,
    MemoryService,
    MemoryType,
    MemoryUpdateRequest,
)
from kira_server.observability import (
    conversation_trace_export,
    doctor_report,
    memory_trace_export,
    project_trace_export,
    replacement_inspection,
    run_trace_export,
)
from kira_server.project_knowledge import ProjectIndexRefreshRequest, ProjectKnowledgeService, ProjectSearchRequest
from kira_server.providers.config import ProviderConfigStore, redact_text
from kira_server.providers.base import ProviderRequest, StreamProvider
from kira_server.providers.fixture import FixtureProvider
from kira_server.providers.openai_compatible import OpenAICompatibleProvider
from kira_server.providers.selection import ProviderMode, select_provider
from kira_server.safety import PermissionDecision, PermissionService
from kira_server.skills.install import install_skill_zip
from kira_server.skills.packages import skill_context_items
from kira_server.skills.registry import SkillRegistry, create_package_skill_registry
from kira_server.storage.database import RuntimeStorage
from kira_server.storage.failure import FailureClass, classify_error_code
from kira_server.transcript import (
    BranchOperationResponse,
    CompactConversationRequest,
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ForkConversationRequest,
    RollbackConversationRequest,
    TranscriptOverflowThresholds,
    TranscriptService,
)
from kira_server.tooling.registry import ToolRegistry

router = APIRouter()


class RunCreateRequest(BaseModel):
    prompt: str | None = None
    task: str | None = None
    project_root: str | None = None
    skill_id: str | None = None
    skill_ids: list[str] = Field(default_factory=list)
    disabled_skill_ids: list[str] = Field(default_factory=list)
    auto_route_skills: bool = False
    project_context_query: str | None = None
    project_context_limit: int = Field(default=5, ge=0, le=20)
    auto_project_context: bool = False
    include_memory: bool = False
    memory_query: str | None = None
    memory_top_k: int = Field(default=5, ge=0, le=20)
    memory_scopes: list[MemoryScope] = Field(default_factory=list)
    memory_types: list[MemoryType] = Field(default_factory=list)
    context_budget: ContextBudget | None = None
    fixture: str | None = None
    provider_mode: ProviderMode = "auto"
    provider: str | None = None
    model: str | None = None
    conversation_id: str | None = None
    overflow_compaction_enabled: bool = True
    transcript_overflow_thresholds: TranscriptOverflowThresholds | None = None

    @model_validator(mode="after")
    def require_prompt_or_task(self) -> "RunCreateRequest":
        if not self.prompt and not self.task:
            raise ValueError("prompt or task is required")
        return self

    @property
    def prompt_text(self) -> str:
        return (self.prompt or self.task or "").strip()


class RunCreateResponse(BaseModel):
    thread_id: str
    conversation_id: str | None = None
    turn_id: str | None = None
    status: RunStatus
    fixture: str | None
    events_url: str
    resume_url: str | None = None
    provider: dict
    skill: dict | None = None
    context: dict | None = None


class RepairNoteRequest(BaseModel):
    note: str
    source: str = "developer"


class CandidateDecisionRequest(BaseModel):
    decision: str
    text: str | None = None


class PermissionPreviewRequest(BaseModel):
    action: str
    subject: dict = Field(default_factory=dict)


class SkillInstallRequest(BaseModel):
    project_root: str = Field(min_length=1)
    zip_path: str = Field(min_length=1)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/doctor")
async def doctor(request: Request) -> dict:
    return doctor_report(
        storage=_runtime_storage(request),
        provider_config=_provider_config(request),
        skill_registry=_skill_registry(request),
        project_knowledge=_project_knowledge(request),
        deep_provider=request.query_params.get("provider_smoke") in {"1", "true", "yes"},
    )


@router.get("/audit")
async def audit_records(request: Request) -> dict:
    limit = _int_query(request, "limit", 100)
    records = _runtime_storage(request).list_audit_records(
        thread_id=request.query_params.get("thread_id"),
        conversation_id=request.query_params.get("conversation_id"),
        project_root=request.query_params.get("project_root"),
        memory_id=request.query_params.get("memory_id"),
        action=request.query_params.get("action"),
        status=request.query_params.get("status"),
        since=request.query_params.get("since"),
        until=request.query_params.get("until"),
        limit=limit,
    )
    return {"records": records, "limit": limit, "truncated": len(records) >= limit, "redacted": True}


@router.post("/permissions/preview", response_model=PermissionDecision)
async def permission_preview(payload: PermissionPreviewRequest, request: Request) -> PermissionDecision:
    return _permission_service(request).evaluate(payload.action, payload.subject)


@router.get("/tools")
async def list_tools(request: Request) -> dict:
    return _tool_registry(request).metadata()


@router.get("/provider/status")
async def provider_status(request: Request) -> dict:
    return _provider_config(request).readiness_metadata()


@router.get("/skills")
async def list_skills(request: Request) -> dict:
    project_root = request.query_params.get("project_root") or _default_project_root()
    include_internal = request.query_params.get("include_internal") in {"1", "true", "yes"}
    return _skill_registry_for_project(request, project_root).metadata(include_internal=include_internal)


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str, request: Request) -> dict:
    include_body = request.query_params.get("include_body") in {"1", "true", "yes"}
    project_root = request.query_params.get("project_root") or _default_project_root()
    skill = _skill_registry_for_project(request, project_root).get_catalog(skill_id, include_body=include_body)
    if skill is None:
        raise HTTPException(status_code=404, detail={"code": "skill_not_found", "message": f"Skill '{skill_id}' was not found"})
    return {"skill": skill.public_metadata()}


@router.post("/skills/install")
async def install_skill(payload: SkillInstallRequest, request: Request) -> dict:
    result = install_skill_zip(project_root=payload.project_root, zip_path=payload.zip_path)
    _audit(
        request,
        action="skill.install",
        status=result.status if result.ok else "error",
        project_root=payload.project_root,
        skill_id=result.skill_id,
        metadata={
            "zip_path": os.path.basename(payload.zip_path),
            "result": result.model_dump(),
        },
        summary=result.message,
    )
    if not result.ok:
        raise HTTPException(status_code=400, detail=result.model_dump())
    return result.model_dump()


@router.post("/runs", response_model=RunCreateResponse)
async def create_run(payload: RunCreateRequest, request: Request) -> RunCreateResponse:
    storage = _runtime_storage(request)
    permission_decisions: list[dict] = []
    audit_ids: list[str] = []
    thread_id = f"local-{uuid4().hex}"
    # Fallback to KIRA_DEFAULT_PROJECT_ROOT so the default agent loop can expose
    # read-only project tools without requiring the frontend to populate a path.
    if not payload.project_root:
        default_root = os.environ.get("KIRA_DEFAULT_PROJECT_ROOT", "").strip()
        if default_root:
            payload.project_root = default_root
    if payload.provider or payload.model:
        provider_known = payload.provider is None or _provider_config(request).get(payload.provider) is not None
        decision = _permission_service(request).evaluate(
            "provider.override",
            {"provider": payload.provider, "model": payload.model, "known": provider_known},
        )
        permission_decisions.append(decision.model_dump())
        audit = storage.record_audit(
            action="provider.override",
            status="allowed" if decision.decision == "allow" else "denied",
            decision=decision.decision,
            thread_id=thread_id,
            provider=payload.provider,
            model=payload.model,
            metadata=decision.model_dump(),
            summary="Provider/model override evaluated",
        )
        audit_ids.append(audit["id"])
        if decision.decision == "deny":
            raise HTTPException(status_code=403, detail=_permission_service(request).error_detail(decision).model_dump())
    transcript = _transcript_service(request)
    if payload.conversation_id:
        conversation = transcript.get_conversation(payload.conversation_id)
        if conversation is None or conversation.archived:
            raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": f"Conversation '{payload.conversation_id}' was not found"})
        overflow_result = None
        if payload.overflow_compaction_enabled:
            overflow_result = transcript.compact_for_overflow_if_needed(
                payload.conversation_id,
                thresholds=payload.transcript_overflow_thresholds,
                context_budget_max_chars=(payload.context_budget.max_chars if payload.context_budget else None),
            )
        transcript_context = transcript.context_for_conversation(payload.conversation_id)
        transcript_items = transcript_context.items
        transcript_trace = transcript_context.trace
        if overflow_result is not None:
            transcript_trace["overflow_compaction"] = overflow_result
    else:
        transcript_items = []
        transcript_trace = None
    requested_skill_ids = [payload.skill_id] if payload.skill_id else []
    requested_skill_ids.extend(skill_id for skill_id in payload.skill_ids if skill_id not in requested_skill_ids)
    requested_skill_ids = [skill_id for skill_id in requested_skill_ids if skill_id not in set(payload.disabled_skill_ids)]
    skill_registry = _skill_registry_for_project(request, payload.project_root)
    auto_routed_skill_id = None
    if not requested_skill_ids:
        routed = skill_registry.route_for_prompt(payload.prompt_text)
        if routed is not None and routed.skill_id not in set(payload.disabled_skill_ids):
            requested_skill_ids = [routed.skill_id]
            auto_routed_skill_id = routed.skill_id
    skill = skill_registry.get(requested_skill_ids[0] if requested_skill_ids else None)
    catalog_skill = skill_registry.get_catalog(requested_skill_ids[0], include_body=True) if requested_skill_ids else None
    if requested_skill_ids and skill is None and catalog_skill is None:
        raise HTTPException(status_code=400, detail={"code": "skill_not_found", "message": f"Skill '{requested_skill_ids[0]}' was not found"})
    if requested_skill_ids and catalog_skill is not None and catalog_skill.package is not None and not catalog_skill.package.valid:
        raise HTTPException(status_code=400, detail={"code": "skill_invalid", "message": f"Skill '{requested_skill_ids[0]}' is not valid"})
    workflow = skill.workflows[0] if skill and skill.workflows else None
    if requested_skill_ids:
        source = catalog_skill.package.source if catalog_skill and catalog_skill.package else None
        source_key = getattr(source, "key", None)
        trusted = source_key in {None, "built-in", "local", "workspace", "project"}
        decision = _permission_service(request).evaluate("skill.invoke", {"skill_id": requested_skill_ids[0], "trusted": trusted, "source": source_key})
        permission_decisions.append(decision.model_dump())
        audit = storage.record_audit(
            action="skill.invoke",
            status="allowed" if decision.decision == "allow" else "approval_required",
            decision=decision.decision,
            thread_id=thread_id,
            skill_id=requested_skill_ids[0],
            metadata=decision.model_dump(),
            summary="Skill invocation policy evaluated",
        )
        audit_ids.append(audit["id"])
    skill_provider_hint = catalog_skill.package.model_hint_profile if catalog_skill and catalog_skill.package else None
    skill_model_hint = catalog_skill.package.model_hint_model if catalog_skill and catalog_skill.package else (skill.model_hint if skill else None)
    selection = select_provider(
        config_store=_provider_config(request),
        provider_mode=payload.provider_mode,
        fixture=payload.fixture,
        provider=payload.provider,
        model=payload.model,
        skill_provider=skill_provider_hint,
        skill_model=skill_model_hint,
    )
    provider_metadata = dict(selection.metadata or {})
    if auto_routed_skill_id:
        provider_metadata["auto_routed_skill_id"] = auto_routed_skill_id
    provider_audit = storage.record_audit(
        action="provider.select",
        status="fallback" if selection.mode == "fixture" and selection.source == "fallback" else "selected",
        decision="allow",
        thread_id=thread_id,
        provider=provider_metadata.get("provider") or provider_metadata.get("attempted_provider", {}).get("provider"),
        model=provider_metadata.get("model") or provider_metadata.get("attempted_provider", {}).get("model"),
        metadata=provider_metadata,
        summary="Provider selected for run",
    )
    audit_ids.append(provider_audit["id"])
    provider_metadata["audit_id"] = provider_audit["id"]
    if permission_decisions:
        provider_metadata["permission"] = permission_decisions[-1]
    context_items = [*transcript_items]
    selected_skill_metadata = []
    # Default behavior: when the run is not bound to an explicit skill, surface
    # the skill catalog so the model can suggest activation. ``auto_route_skills``
    # remains in the request schema for forward compatibility but is no longer
    # required to opt in.
    if not requested_skill_ids:
        context_items.extend(skill_registry.catalog_context_items())
    if catalog_skill and catalog_skill.package:
        context_items.extend(skill_context_items(catalog_skill.package, query=payload.prompt_text))
        selected_skill_metadata.append(catalog_skill.package.public_metadata(include_body=False))
    project_trace = None
    project_query = (payload.project_context_query or "").strip()
    project_query_source = "explicit" if project_query else None
    if not project_query and payload.auto_project_context and payload.project_root:
        project_query = payload.prompt_text
        project_query_source = "prompt"
    if project_query and payload.project_context_limit > 0:
        project_items, project_trace = _project_knowledge(request).context_items_for_query(
            project_query,
            payload.project_root,
            limit=payload.project_context_limit,
            thread_id=thread_id,
        )
        project_trace = {
            **project_trace,
            "auto_project_context": project_query_source == "prompt",
            "query_source": project_query_source,
        }
        context_items.extend(project_items)
    try:
        prepared_turn = transcript.prepare_turn(prompt=payload.prompt_text, thread_id=thread_id, conversation_id=payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": str(exc)}) from exc
    if transcript_trace is None:
        transcript_trace = {
            "conversation_id": prepared_turn.conversation.id,
            "turn_id": prepared_turn.turn.turn_id,
            "active_head_message_id": prepared_turn.previous_head_message_id,
            "included": [],
            "omitted": [],
        }
    else:
        transcript_trace["turn_id"] = prepared_turn.turn.turn_id
    record = _run_store(request).create(
        thread_id=thread_id,
        prompt=payload.prompt_text,
        fixture=selection.fixture,
        provider_mode=selection.mode,
        provider_metadata=provider_metadata,
        provider_selection=selection,
        project_root=payload.project_root,
        skill_id=skill.skill_id if skill else (catalog_skill.skill_id if catalog_skill else None),
        workflow=workflow,
        skill_metadata=_run_skill_metadata(catalog_skill, skill),
        conversation_id=prepared_turn.conversation.id,
        turn_id=prepared_turn.turn.turn_id,
        user_message_id=prepared_turn.user_message.id,
        assistant_message_id=prepared_turn.assistant_message.id,
    )
    memory_trace = None
    if (payload.include_memory or payload.memory_query) and payload.memory_top_k > 0:
        memory_result = _memory_service(request).context_items_for_run(
            thread_id=record.thread_id,
            query=payload.memory_query or payload.prompt_text,
            scopes=payload.memory_scopes,
            types=payload.memory_types,
            top_k=payload.memory_top_k,
        )
        context_items.extend(memory_result.items)
        memory_trace = memory_result.trace
    packed = pack_context(
        thread_id=record.thread_id,
        items=context_items,
        budget=payload.context_budget,
        provider=selection.metadata or {},
        selected_skills=selected_skill_metadata,
        project=project_trace,
        memory=memory_trace,
        transcript=transcript_trace,
    )
    record = _run_store(request).update_context(
        record.thread_id,
        context_items=[item.model_dump() for item in packed.items],
        context_trace={**packed.trace.model_dump(), "audit_ids": audit_ids, "permission_decisions": permission_decisions},
    ) or record
    trace_payload = {**packed.trace.model_dump(), "audit_ids": audit_ids, "permission_decisions": permission_decisions}
    storage.save_context_trace(record.thread_id, trace_payload)
    run_audit = storage.record_audit(
        action="run.create",
        status="created",
        decision="allow",
        thread_id=record.thread_id,
        conversation_id=record.conversation_id,
        turn_id=record.turn_id,
        provider=provider_metadata.get("provider"),
        model=(record.provider_selection.config.model if record.provider_selection.config else (payload.model or skill_model_hint)),
        skill_id=record.skill_id,
        project_root=record.project_root,
        metadata={"context": trace_payload, "provider": provider_metadata},
        summary="Run created",
    )
    audit_ids.append(run_audit["id"])
    storage.create_projection(
        thread_id=record.thread_id,
        status=record.status,
        prompt=record.prompt,
        provider_metadata={**record.provider_metadata, "audit_id": provider_audit["id"], "permission_decisions": permission_decisions},
        fixture=record.fixture,
        skill_metadata=record.skill_metadata,
        workflow_name=(workflow.name if workflow else None),
        project_root=record.project_root,
        model=(record.provider_selection.config.model if record.provider_selection.config else (payload.model or skill_model_hint)),
        conversation_id=record.conversation_id,
        turn_id=record.turn_id,
        user_message_id=record.user_message_id,
        assistant_message_id=record.assistant_message_id,
        transcript_status="streaming",
        active_head_message_id=prepared_turn.previous_head_message_id,
        branch_metadata=transcript_trace.get("branch") if isinstance(transcript_trace, dict) else None,
    )
    return RunCreateResponse(
        thread_id=record.thread_id,
        conversation_id=record.conversation_id,
        turn_id=record.turn_id,
        status=record.status,
        fixture=record.fixture,
        events_url=f"/api/runs/{record.thread_id}/events",
        resume_url=f"/api/runs/{record.thread_id}/resume" if workflow else None,
        provider=record.provider_metadata,
        skill=record.skill_metadata,
        context={
            "included_count": len(packed.items),
            "omitted_count": len(packed.trace.omitted),
            "truncated_count": len(packed.trace.truncated),
            "memory_count": len(memory_trace.get("citations", [])) if memory_trace else 0,
        },
    )


@router.post("/conversations")
async def create_conversation(request: Request, payload: ConversationCreateRequest | None = Body(default=None)) -> dict:
    conversation = _transcript_service(request).create_conversation(payload or ConversationCreateRequest())
    _audit(request, action="transcript.create", status="created", conversation_id=conversation.id, summary="Conversation created")
    return {"conversation": conversation.model_dump()}


@router.get("/conversations")
async def list_conversations(request: Request) -> dict:
    include_archived = request.query_params.get("include_archived") in {"1", "true", "yes"}
    conversations = _transcript_service(request).list_conversations(include_archived=include_archived)
    return {"conversations": [conversation.model_dump() for conversation in conversations]}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request) -> dict:
    conversation = _transcript_service(request).get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": f"Conversation '{conversation_id}' was not found"})
    return {"conversation": conversation.model_dump()}


@router.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, payload: ConversationUpdateRequest, request: Request) -> dict:
    conversation = _transcript_service(request).update_conversation(conversation_id, payload)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": f"Conversation '{conversation_id}' was not found"})
    _audit(request, action="transcript.update", status="updated", conversation_id=conversation_id, metadata=payload.model_dump(), summary="Conversation updated")
    return {"conversation": conversation.model_dump()}


@router.get("/conversations/{conversation_id}/transcript")
async def get_transcript(conversation_id: str, request: Request) -> dict:
    if _transcript_service(request).get_conversation(conversation_id) is None:
        raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": f"Conversation '{conversation_id}' was not found"})
    service = _transcript_service(request)
    messages = service.transcript(conversation_id)
    summaries = service.list_compaction_summaries(conversation_id)
    replacements = service.list_tool_output_replacements(conversation_id=conversation_id)
    branch_records = service.list_branch_records(conversation_id)
    active_head_transitions = service.list_active_head_transitions(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [message.model_dump() for message in messages],
        "compaction_summaries": [summary.model_dump() for summary in summaries],
        "tool_output_replacements": [replacement.model_dump() for replacement in replacements],
        "branch_records": [record.model_dump() for record in branch_records],
        "active_head_transitions": [transition.model_dump() for transition in active_head_transitions],
    }


@router.get("/conversations/{conversation_id}/trace")
async def conversation_trace(conversation_id: str, request: Request) -> dict:
    export = conversation_trace_export(_runtime_storage(request), _transcript_service(request), conversation_id, limit=_int_query(request, "limit", 100))
    if export is None:
        raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": f"Conversation '{conversation_id}' was not found"})
    return export


@router.post("/conversations/{conversation_id}/fork", response_model=BranchOperationResponse)
async def fork_conversation(conversation_id: str, payload: ForkConversationRequest, request: Request) -> BranchOperationResponse:
    try:
        response = _transcript_service(request).fork_conversation(conversation_id, payload)
        _audit(request, action="transcript.fork", status="completed", conversation_id=conversation_id, metadata=response.model_dump(), summary="Conversation branch forked")
        return response
    except ValueError as exc:
        raise _branch_http_error(str(exc)) from exc


@router.post("/conversations/{conversation_id}/rollback", response_model=BranchOperationResponse)
async def rollback_conversation(conversation_id: str, payload: RollbackConversationRequest, request: Request) -> BranchOperationResponse:
    try:
        response = _transcript_service(request).rollback_conversation(conversation_id, payload)
        _audit(request, action="transcript.rollback", status="completed", conversation_id=conversation_id, metadata=response.model_dump(), summary="Conversation branch rolled back")
        return response
    except ValueError as exc:
        raise _branch_http_error(str(exc)) from exc


@router.post("/conversations/{conversation_id}/compact")
async def compact_conversation(conversation_id: str, payload: CompactConversationRequest, request: Request) -> dict:
    service = _transcript_service(request)
    conversation = service.get_conversation(conversation_id)
    if conversation is None or conversation.archived:
        raise HTTPException(
            status_code=404,
            detail={"code": "conversation_not_found", "message": f"Conversation '{conversation_id}' was not found"},
        )
    metadata: dict | None = None
    summary_text: str | None = None
    if payload.summarizer_mode == "real":
        selection = select_provider(
            config_store=_provider_config(request),
            provider_mode="real",
            provider=payload.provider,
            model=payload.model,
        )
        metadata = selection.metadata or {}
        if selection.mode == "real":
            summary_text = await _real_compaction_summary(conversation_id, payload, selection, _openai_provider(request), service)
    try:
        response = service.compact_conversation(
            conversation_id,
            payload,
            summarizer_metadata=metadata,
            summary_text=summary_text,
        )
    except ValueError as exc:
        code = str(exc)
        status_code = 404 if code in {"conversation_not_found", "conversation_archived"} else 400
        raise HTTPException(status_code=status_code, detail={"code": code, "message": code}) from exc
    _audit(request, action="transcript.compact", status="completed", conversation_id=conversation_id, metadata=response.model_dump(), summary="Conversation compacted")
    return response.model_dump()


@router.get("/conversations/{conversation_id}/context")
async def get_conversation_context(conversation_id: str, request: Request) -> dict:
    if _transcript_service(request).get_conversation(conversation_id) is None:
        raise HTTPException(status_code=404, detail={"code": "conversation_not_found", "message": f"Conversation '{conversation_id}' was not found"})
    context = _transcript_service(request).context_for_conversation(conversation_id)
    _audit(request, action="transcript.context", status="read", conversation_id=conversation_id, metadata=context.trace, summary="Conversation context exported")
    return {"conversation_id": conversation_id, "items": [item.model_dump() for item in context.items], "trace": context.trace}


@router.get("/memory")
async def list_memory(request: Request) -> dict:
    search = MemorySearchRequest(
        query=request.query_params.get("query") or "",
        scopes=_multi_query(request, "scope"),
        types=_multi_query(request, "type"),
        statuses=_multi_query(request, "status") or ["active"],
        tags=_multi_query(request, "tag"),
        project_root_id=request.query_params.get("project_root_id"),
        thread_id=request.query_params.get("thread_id"),
        top_k=_int_query(request, "limit", 50),
        include_non_injectable=request.query_params.get("include_non_injectable") in {"1", "true", "yes"},
    )
    records = _memory_service(request).list(search)
    return {"memories": [record.model_dump() for record in records]}


@router.post("/memory")
async def create_memory(payload: MemoryCreateRequest, request: Request) -> dict:
    decision = _permission_service(request).evaluate("memory.write", payload.model_dump())
    try:
        record = _memory_service(request).create(payload)
    except ValueError as exc:
        _audit(request, action="memory.create", status="rejected", decision=decision.decision, metadata={"error": str(exc), "payload": payload.model_dump()}, summary="Memory create rejected")
        raise HTTPException(status_code=400, detail={"code": "memory_guard_rejected", "message": str(exc)}) from exc
    _audit(request, action="memory.create", status="created", decision=decision.decision, memory_id=record.id, metadata={"memory": record.model_dump(), "permission": decision.model_dump()}, summary="Memory created")
    return {"memory": record.model_dump()}


@router.get("/memory/candidates")
async def list_memory_candidates(request: Request) -> dict:
    candidates = _memory_service(request).list_candidates(request.query_params.get("thread_id"))
    return {"candidates": [candidate.model_dump() for candidate in candidates]}


@router.post("/memory/extract")
async def extract_memory(payload: ExtractionRequest, request: Request) -> dict:
    result = _memory_service(request).extract(payload)
    _audit(request, action="memory.extract", status="completed", thread_id=payload.thread_id, metadata=result, summary="Memory extraction completed")
    return result


@router.post("/memory/search")
async def search_memory(payload: MemorySearchRequest, request: Request) -> dict:
    response = _memory_service(request).search(payload)
    _audit(request, action="memory.search", status="completed", thread_id=payload.thread_id, metadata=response.model_dump(), summary="Memory search completed")
    return response.model_dump()


@router.get("/memory/trace")
async def memory_trace(request: Request) -> dict:
    return memory_trace_export(
        _runtime_storage(request),
        memory_id=request.query_params.get("memory_id"),
        thread_id=request.query_params.get("thread_id"),
        limit=_int_query(request, "limit", 100),
    )


@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str, request: Request) -> dict:
    record = _memory_service(request).get(memory_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "memory_not_found", "message": f"Memory '{memory_id}' was not found"})
    return {"memory": record.model_dump()}


@router.put("/memory/{memory_id}")
async def update_memory(memory_id: str, payload: MemoryUpdateRequest, request: Request) -> dict:
    decision = _permission_service(request).evaluate("memory.write", {"memory_id": memory_id, **payload.model_dump(exclude_none=True)})
    try:
        record = _memory_service(request).update(memory_id, payload)
    except ValueError as exc:
        _audit(request, action="memory.update", status="rejected", decision=decision.decision, memory_id=memory_id, metadata={"error": str(exc), "payload": payload.model_dump()}, summary="Memory update rejected")
        raise HTTPException(status_code=400, detail={"code": "memory_guard_rejected", "message": str(exc)}) from exc
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "memory_not_found", "message": f"Memory '{memory_id}' was not found"})
    _audit(request, action="memory.update", status="updated", decision=decision.decision, memory_id=memory_id, metadata={"memory": record.model_dump(), "permission": decision.model_dump()}, summary="Memory updated")
    return {"memory": record.model_dump()}


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str, request: Request) -> dict:
    if not _memory_service(request).delete(memory_id):
        raise HTTPException(status_code=404, detail={"code": "memory_not_found", "message": f"Memory '{memory_id}' was not found"})
    _audit(request, action="memory.delete", status="deleted", memory_id=memory_id, summary="Memory deleted")
    return {"deleted": True, "memory_id": memory_id}


@router.post("/memory/{memory_id}/actions")
async def memory_action(memory_id: str, payload: MemoryActionRequest, request: Request) -> dict:
    try:
        result = _memory_service(request).action(memory_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "memory_action_rejected", "message": str(exc)}) from exc
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "memory_not_found", "message": f"Memory '{memory_id}' was not found"})
    _audit(request, action=f"memory.{payload.action}", status="completed", memory_id=memory_id, metadata=result, summary="Memory lifecycle action completed")
    return result


@router.post("/memory/candidates/{candidate_id}/decisions")
async def memory_candidate_decision(candidate_id: str, payload: CandidateDecisionRequest, request: Request) -> dict:
    try:
        result = _memory_service(request).candidate_decision(candidate_id, payload.decision, text=payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "candidate_decision_rejected", "message": str(exc)}) from exc
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "candidate_not_found", "message": f"Candidate '{candidate_id}' was not found"})
    _audit(request, action="memory.candidate_decision", status="completed", metadata={"candidate_id": candidate_id, "result": result}, summary="Memory candidate decision recorded")
    return result


@router.get("/runs/{thread_id}/events")
async def run_events(thread_id: str, request: Request) -> StreamingResponse:
    store = _run_store(request)
    record = store.get(thread_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{thread_id}' was not found")
    after_seq = _int_query(request, "after_seq", 0)

    async def stream():
        storage = _runtime_storage(request)
        for replayed in storage.list_events(thread_id, after_seq=after_seq):
            yield _to_sse(replayed)
        if record.status in {"completed", "error", "stopped", "waiting_for_user"}:
            return
        acquired = True
        if record.workflow is not None:
            acquired, lock = storage.acquire_lock(thread_id)
            if not acquired:
                conflict = storage.append_event(
                    thread_id=thread_id,
                    event_type="error",
                    data={
                        "code": "run_lock_conflict",
                        "message": "Run already has an active executor",
                        "metadata": {"lock": lock},
                    },
                )
                yield _to_sse(conflict)
                return
        store.set_status(thread_id, "running")
        storage.update_projection(thread_id, status="running")
        storage.record_audit(action="workflow.start", status="started", thread_id=thread_id, skill_id=record.skill_id, metadata={"workflow": getattr(record.workflow, "name", None)}, summary="Workflow/run execution started")
        attempt_id = storage.create_attempt(
            thread_id=thread_id,
            skill_id=record.skill_id,
            model=(record.provider_selection.config.model if record.provider_selection.config else None),
            durability_mode="sqlite" if record.workflow is not None else "direct",
        )
        storage.record_provider_attempt(
            thread_id=thread_id,
            provider_metadata=record.provider_metadata,
            status="started",
            retry_count=(record.provider_selection.config.retry.attempts if record.provider_selection.config else 0),
            timeout=(record.provider_selection.config.timeout if record.provider_selection.config else None),
        )
        storage.record_audit(action="provider.attempt", status="started", thread_id=thread_id, provider=record.provider_metadata.get("provider"), model=record.provider_metadata.get("model"), metadata=record.provider_metadata, summary="Provider attempt started")
        provider_events = await _record_events(record, request)
        failure_class = failure_class_for_events(provider_events)
        storage.record_provider_attempt(
            thread_id=thread_id,
            provider_metadata=record.provider_metadata,
            status="error" if failure_class else "completed",
            retry_count=(record.provider_selection.config.retry.attempts if record.provider_selection.config else 0),
            timeout=(record.provider_selection.config.timeout if record.provider_selection.config else None),
            error_summary=(failure_class.value if failure_class else None),
        )
        storage.record_audit(
            action="provider.attempt",
            status="error" if failure_class else "completed",
            thread_id=thread_id,
            provider=record.provider_metadata.get("provider"),
            model=record.provider_metadata.get("model"),
            metadata={"failure_class": failure_class.value if failure_class else None, "provider": record.provider_metadata},
            summary="Provider attempt completed",
        )
        for provider_event in provider_events:
            data = dict(provider_event.data)
            data["provider"] = _stable_provider_metadata(record.provider_metadata)
            if record.skill_metadata:
                data["skill"] = record.skill_metadata
            event = storage.append_event(thread_id=thread_id, event_type=provider_event.type, data=data)
            _transcript_service(request).append_event(thread_id, provider_event.type, data)
            if provider_event.type == "error":
                store.set_status(thread_id, "error")
                storage.update_projection(thread_id, status="error", failure_class=(failure_class or classify_error_code(str(data.get("code")))).value)
            elif provider_event.type == "interrupt":
                storage.record_audit(action="hitl.interrupt", status="waiting", thread_id=thread_id, skill_id=record.skill_id, metadata=data, summary="Workflow interrupted for human input")
                store.set_status(thread_id, "waiting_for_user")
                storage.update_projection(thread_id, status="waiting_for_user", pending_interrupt=data)
            elif provider_event.type == "done":
                store.set_status(thread_id, "completed")
                storage.clear_pending_interrupt(thread_id, status="completed")
            elif provider_event.type == "tool_result" and data.get("name") == "run_shell_command":
                storage.record_audit(
                    action="shell.run",
                    status=str(data.get("status") or "completed"),
                    decision="allow",
                    thread_id=thread_id,
                    skill_id=record.skill_id,
                    tool="run_shell_command",
                    project_root=record.project_root,
                    metadata={"result": data.get("result")},
                    summary="Shell command completed through agent tool",
                )
            yield _to_sse(event)
        if not any(event.type in {"done", "error", "interrupt"} for event in provider_events):
            done = storage.append_event(thread_id=thread_id, event_type="done", data={"message": "Run completed", "provider": _stable_provider_metadata(record.provider_metadata)})
            _transcript_service(request).append_event(thread_id, "done", done.data)
            store.set_status(thread_id, "completed")
            storage.update_projection(thread_id, status="completed")
            yield _to_sse(done)
        interrupted = any(event.type == "interrupt" for event in provider_events)
        storage.finish_attempt(attempt_id, status="interrupted" if interrupted else ("error" if failure_class else "completed"), failure_class=(failure_class.value if failure_class else None))
        storage.record_audit(action="workflow.finish", status="interrupted" if interrupted else ("error" if failure_class else "completed"), thread_id=thread_id, skill_id=record.skill_id, metadata={"failure_class": failure_class.value if failure_class else None}, summary="Workflow/run execution finished")
        if acquired:
            storage.release_lock(thread_id)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/runs/{thread_id}/trace")
async def run_trace(thread_id: str, request: Request) -> dict:
    export = run_trace_export(_runtime_storage(request), thread_id, limit=_int_query(request, "limit", 100))
    if export is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    return export


@router.get("/runs/{thread_id}/state")
async def run_state(thread_id: str, request: Request) -> dict:
    state = _runtime_storage(request).state_projection(thread_id)
    if state is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    return state


@router.get("/runs/{thread_id}/replay")
async def run_replay(thread_id: str, request: Request) -> dict:
    export = _runtime_storage(request).debug_export(thread_id)
    if export is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    return export


@router.get("/runs/{thread_id}/context")
async def run_context(thread_id: str, request: Request) -> dict:
    trace = _runtime_storage(request).get_context_trace(thread_id)
    if trace is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    return trace


@router.get("/project/index/status")
async def project_index_status(request: Request) -> dict:
    return _project_knowledge(request).status(request.query_params.get("root"))


@router.post("/project/index/refresh")
async def project_index_refresh(payload: ProjectIndexRefreshRequest, request: Request) -> dict:
    result = _project_knowledge(request).refresh(payload)
    _audit(request, action="project.index_refresh", status="completed", project_root=payload.root, metadata=result, summary="Project index refresh completed")
    return result


@router.post("/project/search")
async def project_search(payload: ProjectSearchRequest, request: Request) -> dict:
    result = _project_knowledge(request).search(payload)
    _audit(request, action="project.search", status="completed", project_root=payload.root, metadata=result, summary="Project search completed")
    return result


@router.get("/project/trace")
async def project_trace(request: Request) -> dict:
    return project_trace_export(_runtime_storage(request), request.query_params.get("root"), limit=_int_query(request, "limit", 100))


@router.get("/project/file")
async def project_file(path: str, request: Request) -> dict:
    root = request.query_params.get("root")
    result = _project_knowledge(request).read_file(path=path, root=root)
    _audit(request, action="project.file_read", status="completed", project_root=root, metadata={"path": path, "result": result}, summary="Project file read completed")
    return result


@router.post("/runs/{thread_id}/cancel")
async def cancel_run(thread_id: str, request: Request) -> dict:
    store = _run_store(request)
    if _runtime_storage(request).state_projection(thread_id) is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    store.set_status(thread_id, "stopped")
    _runtime_storage(request).update_projection(thread_id, status="cancelled", failure_class=FailureClass.CANCELLED.value)
    _runtime_storage(request).release_lock(thread_id, status="cancelled")
    _audit(request, action="workflow.cancel", status="cancelled", thread_id=thread_id, summary="Run cancelled")
    event = _runtime_storage(request).append_event(
        thread_id=thread_id,
        event_type="error",
        data={"code": "cancelled", "message": "Run cancelled"},
    )
    _transcript_service(request).mark_cancelled(thread_id)
    return {"status": "cancelled", "event": event.model_dump()}


@router.post("/runs/{thread_id}/resume", response_model=ResumeResult)
async def resume_run(thread_id: str, request: Request, payload: ResumeRequest | None = Body(default=None)) -> ResumeResult:
    storage = _runtime_storage(request)
    state = storage.state_projection(thread_id)
    if state is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    if state["status"] in {"completed", "cancelled", "error"}:
        raise HTTPException(
            status_code=409,
            detail={"code": "terminal_run", "message": f"Run '{thread_id}' is terminal and cannot be resumed"},
        )
    pending = state.get("pending_interrupt")
    if not pending:
        raise HTTPException(status_code=409, detail={"code": "no_pending_interrupt", "message": "Run is not waiting on human input"})
    if payload is None:
        raise HTTPException(status_code=400, detail={"code": "invalid_resume", "message": "Resume payload is required"})
    try:
        validated = validate_resume_for_interrupt(pending, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_resume", "message": str(exc)}) from exc
    branch_conflict = _transcript_service(request).resume_conflict_for_thread(thread_id)
    if branch_conflict:
        _audit(request, action="hitl.resume", status="rejected", thread_id=thread_id, metadata=branch_conflict, summary="Resume rejected for inactive branch")
        raise HTTPException(
            status_code=409,
            detail={
                "code": "inactive_branch_conflict",
                "message": "Run belongs to an inactive conversation branch and cannot be resumed",
                "metadata": branch_conflict,
            },
        )
    acquired, lock = storage.acquire_lock(thread_id)
    if not acquired:
        raise HTTPException(status_code=409, detail={"code": "run_lock_conflict", "message": "Run already has an active executor", "lock": lock})
    record = _run_store(request).get(thread_id)
    if record is None or record.workflow is None or record.skill_id is None:
        storage.release_lock(thread_id)
        raise HTTPException(status_code=409, detail={"code": "resume_context_missing", "message": "Resume requires an active skill graph run context"})
    storage.clear_pending_interrupt(thread_id, status="running")
    storage.record_audit(action="hitl.resume", status="accepted", thread_id=thread_id, metadata=validated.model_dump(), summary="Human input resume accepted")
    resume_event = storage.append_event(
        thread_id=thread_id,
        event_type="resume",
        data={
            "interrupt_id": validated.interrupt_id,
            "decision": validated.decision,
            "value": validated.value,
            "reason": validated.reason,
            "data": validated.data,
        },
    )
    _transcript_service(request).append_event(thread_id, "resume", resume_event.data)
    context = _graph_context_for_record(record, request)
    continuation = await _graph_runtime(request).resume(context, validated, pending)
    persisted = [resume_event]
    failure_class = failure_class_for_events(continuation)
    for provider_event in continuation:
        data = dict(provider_event.data)
        data["provider"] = _stable_provider_metadata(record.provider_metadata)
        if record.skill_metadata:
            data["skill"] = record.skill_metadata
        event = storage.append_event(thread_id=thread_id, event_type=provider_event.type, data=data)
        _transcript_service(request).append_event(thread_id, provider_event.type, data)
        persisted.append(event)
        if provider_event.type == "error":
            _run_store(request).set_status(thread_id, "error")
            storage.update_projection(thread_id, status="error", failure_class=(failure_class or classify_error_code(str(data.get("code")))).value)
        elif provider_event.type == "done":
            _run_store(request).set_status(thread_id, "completed")
            storage.clear_pending_interrupt(thread_id, status="completed")
    storage.release_lock(thread_id)
    storage.record_audit(action="workflow.resume_finish", status="completed" if any(event.type == "done" for event in persisted) else "running", thread_id=thread_id, metadata={"event_count": len(persisted)}, summary="Workflow resume finished")
    return ResumeResult(
        status="completed" if any(event.type == "done" for event in persisted) else "running",
        thread_id=thread_id,
        interrupt_id=validated.interrupt_id,
        decision=validated.decision,
        events=[event.model_dump() for event in persisted],
    )


@router.post("/runs/{thread_id}/repair-notes")
async def add_repair_note(thread_id: str, payload: RepairNoteRequest, request: Request) -> dict:
    if _runtime_storage(request).state_projection(thread_id) is None:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": f"Run '{thread_id}' was not found"})
    if any(token in payload.note.lower() for token in ("api_key", "sk-", "provider secret")):
        raise HTTPException(status_code=400, detail={"code": "unsafe_repair", "message": "Repair note appears to include a secret"})
    result = _runtime_storage(request).add_repair_note(thread_id=thread_id, note=payload.note, source=payload.source)
    _audit(request, action="repair.note", status="created", thread_id=thread_id, metadata=result, summary="Repair note added")
    return result


@router.get("/replacements/{replacement_id}/inspect")
async def inspect_replacement(replacement_id: str, request: Request) -> dict:
    result = replacement_inspection(_runtime_storage(request), _transcript_service(request), replacement_id, _permission_service(request))
    if result.get("status") == "missing":
        raise HTTPException(status_code=404, detail={"code": "replacement_not_found", "message": f"Replacement '{replacement_id}' was not found", "metadata": result})
    if result.get("status") == "denied":
        raise HTTPException(status_code=403, detail={"code": "replacement_inspection_denied", "message": result.get("reason"), "metadata": result})
    return result


def _to_sse(event: KiraEvent) -> str:
    payload = json.dumps(event.model_dump(), ensure_ascii=False)
    return f"event: {event.type}\ndata: {payload}\n\n"


def _stable_provider_metadata(metadata: dict) -> dict:
    provider = dict(metadata)
    provider.pop("audit_id", None)
    permission = provider.get("permission")
    if isinstance(permission, dict):
        permission = dict(permission)
        permission.pop("created_at", None)
        provider["permission"] = permission
    return provider


def _branch_http_error(code: str) -> HTTPException:
    if code in {"conversation_not_found", "source_message_not_found", "target_message_not_found", "source_turn_not_found", "target_turn_not_found"}:
        return HTTPException(status_code=404, detail={"code": code, "message": code})
    if code in {"source_inactive", "target_inactive", "conversation_archived", "source_required", "target_required"}:
        return HTTPException(status_code=409 if code.endswith("_inactive") else 400, detail={"code": code, "message": code})
    return HTTPException(status_code=400, detail={"code": code, "message": code})


async def _record_events(record, request: Request):
    provider = _fixture_provider(request) if record.provider_mode == "fixture" else _openai_provider(request)
    provider_request = ProviderRequest(
        prompt=record.prompt,
        fixture=record.fixture,
        model=(record.provider_selection.config.model if record.provider_selection.config else None),
        provider_metadata=record.provider_metadata,
        config=record.provider_selection.config,
        context_items=record.context_items,
    )
    if record.workflow is None or record.skill_id is None:
        # Fixture mode keeps the legacy passthrough path: deterministic
        # canned events do not need function-calling and existing tests
        # rely on that exact stream.
        if record.provider_mode == "fixture":
            return [event async for event in provider.stream(provider_request)]

        # Default no-skill code path: drive the agent loop so the model can
        # call read-only project tools when a project_root is bound to the
        # run. Without a project_root we still go through the loop with an
        # empty tool list to keep behavior uniform — the loop becomes a
        # transparent passthrough in that case.
        context_items = list(record.context_items or [])
        has_skill_catalog = any(item.get("kind") == "skill_summary" for item in context_items)
        allowed_tools: list[str] = []
        if record.project_root:
            allowed_tools = ["list_project_files", "search_project_files", "read_project_file", "run_shell_command"]
        system_prompt = build_default_system_prompt(
            tool_names=allowed_tools,
            has_skills=has_skill_catalog,
        )
        return [
            event
            async for event in run_default_agent(
                provider=provider,
                base_request=provider_request,
                tool_registry=_tool_registry(request),
                allowed_tools=allowed_tools,
                system_prompt=system_prompt,
                context_items=context_items,
                user_message=record.prompt,
            )
        ]

    return await _graph_runtime(request).run(_graph_context_for_record(record, request, provider=provider, provider_request=provider_request))


async def _real_compaction_summary(
    conversation_id: str,
    payload: CompactConversationRequest,
    selection,
    provider: StreamProvider,
    service: TranscriptService,
) -> str | None:
    messages = service.transcript(conversation_id)
    visible_blocks = []
    for message in messages:
        if message.role not in {"user", "assistant"}:
            continue
        text = "".join(part.text for part in message.parts if part.visible and part.kind == "text").strip()
        if text:
            visible_blocks.append(f"{message.role} {message.id}: {text}")
    if payload.tail_messages > 0 and len(visible_blocks) > payload.tail_messages:
        visible_blocks = visible_blocks[:-payload.tail_messages]
    if not visible_blocks:
        return None
    prompt = (
        "Summarize the following local conversation transcript for future context. "
        "Preserve user goals, constraints, decisions, unresolved questions, selected skills, project root context, "
        "bounded tool outcomes, and source references. Exclude secrets, provider config, hidden thinking, and raw tool output.\n\n"
        + "\n".join(visible_blocks)
    )
    try:
        chunks: list[str] = []
        request = ProviderRequest(
            prompt=prompt,
            fixture="summary",
            model=(selection.config.model if selection.config else None),
            provider_metadata=selection.metadata,
            config=selection.config,
            context_items=[],
        )
        async for event in provider.stream(request):
            if event.type == "text_delta" and isinstance(event.data.get("text"), str):
                chunks.append(event.data["text"])
            if event.type == "error":
                return None
        summary = redact_text("".join(chunks).strip())
        return summary[:2_400] if summary else None
    except Exception:
        return None


def _graph_context_for_record(record, request: Request, provider=None, provider_request: ProviderRequest | None = None) -> GraphRuntimeContext:
    resolved_provider = provider or (_fixture_provider(request) if record.provider_mode == "fixture" else _openai_provider(request))
    resolved_request = provider_request or ProviderRequest(
        prompt=record.prompt,
        fixture=record.fixture,
        model=(record.provider_selection.config.model if record.provider_selection.config else None),
        provider_metadata=record.provider_metadata,
        config=record.provider_selection.config,
        context_items=record.context_items,
    )
    return GraphRuntimeContext(
        prompt=record.prompt,
        thread_id=record.thread_id,
        skill_id=record.skill_id,
        workflow=record.workflow,
        project_root=record.project_root,
        provider=resolved_provider,
        provider_request=resolved_request,
        provider_metadata=record.provider_metadata,
        runtime_storage=_runtime_storage(request),
    )


def _run_store(request: Request) -> InMemoryRunStore:
    return request.app.state.run_store


def _fixture_provider(request: Request) -> FixtureProvider:
    return request.app.state.fixture_provider


def _openai_provider(request: Request) -> OpenAICompatibleProvider:
    return request.app.state.openai_provider


def _provider_config(request: Request) -> ProviderConfigStore:
    return request.app.state.provider_config


def _tool_registry(request: Request) -> ToolRegistry:
    return request.app.state.tool_registry


def _skill_registry(request: Request) -> SkillRegistry:
    return request.app.state.skill_registry


def _skill_registry_for_project(request: Request, project_root: str | None) -> SkillRegistry:
    if not project_root:
        return _skill_registry(request)
    return create_package_skill_registry(project_root=project_root)


def _run_skill_metadata(catalog_skill, skill) -> dict | None:
    selected = catalog_skill or skill
    if selected is None:
        return None
    package = getattr(selected, "package", None)
    if package is not None:
        return package.public_metadata(include_body=False)
    return selected.public_metadata()


def _default_project_root() -> str | None:
    value = os.environ.get("KIRA_DEFAULT_PROJECT_ROOT", "").strip()
    return value or None


def _graph_runtime(request: Request) -> GraphRuntime:
    return request.app.state.graph_runtime


def _runtime_storage(request: Request) -> RuntimeStorage:
    return request.app.state.runtime_storage


def _project_knowledge(request: Request) -> ProjectKnowledgeService:
    return request.app.state.project_knowledge


def _memory_service(request: Request) -> MemoryService:
    return request.app.state.memory_service


def _transcript_service(request: Request) -> TranscriptService:
    return request.app.state.transcript_service


def _permission_service(request: Request) -> PermissionService:
    return request.app.state.permission_service


def _audit(
    request: Request,
    *,
    action: str,
    status: str,
    decision: str | None = "allow",
    thread_id: str | None = None,
    conversation_id: str | None = None,
    turn_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    tool: str | None = None,
    skill_id: str | None = None,
    memory_id: str | None = None,
    project_root: str | None = None,
    metadata: dict | None = None,
    summary: str | None = None,
) -> dict:
    return _runtime_storage(request).record_audit(
        action=action,
        status=status,
        decision=decision,
        thread_id=thread_id,
        conversation_id=conversation_id,
        turn_id=turn_id,
        provider=provider,
        model=model,
        tool=tool,
        skill_id=skill_id,
        memory_id=memory_id,
        project_root=project_root,
        metadata=metadata,
        summary=summary,
    )


def _int_query(request: Request, name: str, default: int) -> int:
    raw = request.query_params.get(name)
    if raw is None:
        return default
    try:
        return max(int(raw), 0)
    except ValueError:
        return default


def _multi_query(request: Request, name: str) -> list:
    values = request.query_params.getlist(name)
    if not values:
        raw = request.query_params.get(f"{name}s")
        values = raw.split(",") if raw else []
    return [value for value in (item.strip() for item in values) if value]
