from __future__ import annotations

from typing import Any, TypedDict


class KiraGraphState(TypedDict, total=False):
    prompt: str
    thread_id: str
    skill_id: str
    workflow_name: str
    project_root: str | None
    provider_metadata: dict[str, Any]
    model: str | None
    fixture_fallback: bool
    events: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    pending_interrupt: dict[str, Any] | None
    public_state: dict[str, Any]


def public_graph_state(state: KiraGraphState) -> dict[str, Any]:
    return {
        "prompt": state.get("prompt"),
        "thread_id": state.get("thread_id"),
        "skill_id": state.get("skill_id"),
        "workflow_name": state.get("workflow_name"),
        "project_root": state.get("project_root"),
        "provider_metadata": state.get("provider_metadata") or {},
        "model": state.get("model"),
        "fixture_fallback": bool(state.get("fixture_fallback")),
        "tool_results": state.get("tool_results") or [],
        "errors": state.get("errors") or [],
        "pending_interrupt": state.get("pending_interrupt"),
    }
