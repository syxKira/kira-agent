from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, StateGraph
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
except Exception:  # pragma: no cover - optional dependency API differs by version
    SqliteSaver = None  # type: ignore[assignment]

from kira_server.core.events import ProviderEvent
from kira_server.graph_runtime.events import append_event, append_events, events_from_state
from kira_server.graph_runtime.hitl import ResumeRequest, make_interrupt
from kira_server.graph_runtime.specs import END_NODE, WorkflowNodeSpec, WorkflowSpec
from kira_server.graph_runtime.state import KiraGraphState, public_graph_state
from kira_server.graph_runtime.streaming import normalize_graph_events
from kira_server.graph_runtime.toolnode import ToolNodeDispatcher, create_toolnode_dispatcher
from kira_server.graph_runtime.validation import WorkflowValidationError, validate_workflow
from kira_server.providers.base import ProviderRequest, StreamProvider
from kira_server.storage.database import RuntimeStorage
from kira_server.storage.failure import FailureClass, classify_error_code
from kira_server.tooling.registry import ToolRegistry


@dataclass(frozen=True)
class GraphRuntimeContext:
    prompt: str
    thread_id: str
    skill_id: str
    workflow: WorkflowSpec
    project_root: str | None
    provider: StreamProvider
    provider_request: ProviderRequest
    provider_metadata: dict[str, Any]
    runtime_storage: RuntimeStorage | None = None


class GraphRuntime:
    def __init__(self, tool_registry: ToolRegistry, runtime_storage: RuntimeStorage | None = None) -> None:
        self._tool_registry = tool_registry
        self._runtime_storage = runtime_storage

    def compile(self, workflow: WorkflowSpec):
        validate_workflow(workflow, registered_tools=set(self._tool_registry.tool_names))
        graph = StateGraph(KiraGraphState)
        tool_dispatcher = create_toolnode_dispatcher(self._tool_registry, workflow.tools)

        for node in workflow.nodes:
            graph.add_node(node.id, self._node_callable(node, tool_dispatcher))

        graph.set_entry_point(workflow.entrypoint)
        for edge in workflow.edges:
            graph.add_edge(edge.source, _target(edge.target))
        for edge in workflow.conditional_edges:
            graph.add_conditional_edges(
                edge.source,
                _condition(edge.condition),
                {route: _target(target) for route, target in edge.routes.items()},
            )
        return graph.compile()

    async def run(self, context: GraphRuntimeContext) -> list[ProviderEvent]:
        try:
            graph = self.compile(context.workflow)
            bind_runtime_context(context)
            final_state = await graph.ainvoke(
                self._initial_state(context),
                config={"configurable": {"thread_id": context.thread_id}},
            )
            storage = context.runtime_storage or self._runtime_storage
            if storage:
                storage.save_checkpoint(thread_id=context.thread_id, checkpoint_id="latest", state=final_state)
            events = normalize_graph_events(events_from_state(final_state))
            if storage and events and not any(event.type == "error" for event in events):
                events.append(ProviderEvent(type="checkpoint", data={"checkpoint_id": "latest", "workflow": context.workflow.name}))
            if not any(event.type in {"error", "interrupt"} for event in events):
                events.append(ProviderEvent(type="done", data={"message": "Graph run completed"}))
            return events
        except WorkflowValidationError as exc:
            return [
                ProviderEvent(
                    type="error",
                    data={"code": exc.code, "message": exc.message, "metadata": {"errors": exc.errors}},
                )
            ]
        except Exception as exc:
            return [
                ProviderEvent(
                    type="error",
                    data={
                        "code": "graph_runtime_error",
                        "message": "Graph execution failed",
                        "metadata": {"error_type": type(exc).__name__, "error": str(exc)},
                    },
                )
            ]
        finally:
            clear_runtime_context()

    async def resume(self, context: GraphRuntimeContext, resume: ResumeRequest, pending_interrupt: dict[str, Any]) -> list[ProviderEvent]:
        bind_runtime_context(context)
        try:
            decision = resume.decision
            kind = str(pending_interrupt.get("kind") or "approval")
            base = {
                "interrupt_id": resume.interrupt_id,
                "decision": decision,
                "kind": kind,
            }
            if decision == "reject":
                return [
                    ProviderEvent(type="tool_result", data={**base, "name": "human_decision", "status": "rejected", "result": {"reason": resume.reason or resume.value}}),
                    ProviderEvent(type="done", data={"message": "Run completed after human rejection"}),
                ]
            if kind == "edit":
                return [
                    ProviderEvent(type="text_delta", data={"text": f"Edited value accepted: {resume.value}"}),
                    ProviderEvent(type="done", data={"message": "Run completed after edit"}),
                ]
            if kind == "question":
                answer = resume.value or resume.data.get("answer") or ""
                return [
                    ProviderEvent(type="text_delta", data={"text": f"Answer received: {answer}"}),
                    ProviderEvent(type="done", data={"message": "Run completed after answer"}),
                ]
            if kind == "python_approval":
                return [
                    ProviderEvent(type="tool_result", data={**base, "name": "run_python_script", "status": "approved", "result": {"approved": True}}),
                    ProviderEvent(type="done", data={"message": "Run completed after Python approval"}),
                ]
            return [
                ProviderEvent(type="text_delta", data={"text": "Approval received. Continuing the workflow."}),
                ProviderEvent(type="done", data={"message": "Run completed after approval"}),
            ]
        finally:
            clear_runtime_context()

    def _initial_state(self, context: GraphRuntimeContext) -> KiraGraphState:
        return {
            "prompt": context.prompt,
            "thread_id": context.thread_id,
            "skill_id": context.skill_id,
            "workflow_name": context.workflow.name,
            "project_root": context.project_root,
            "provider_metadata": context.provider_metadata,
            "model": context.provider_request.model,
            "fixture_fallback": context.provider_metadata.get("mode") == "fixture",
            "events": [],
            "tool_results": [],
            "errors": [],
            "pending_interrupt": None,
            "public_state": {},
        }

    def _node_callable(
        self,
        node: WorkflowNodeSpec,
        tool_dispatcher: ToolNodeDispatcher,
    ) -> Callable[[KiraGraphState], Any]:
        if node.node_type == "model":
            return self._model_node
        if node.node_type == "tool":
            return _tool_node(node, tool_dispatcher)
        if node.node_type == "interrupt":
            return _interrupt_node(node)
        return _passthrough_node

    async def _model_node(self, state: KiraGraphState) -> dict[str, Any]:
        context = _runtime_context(state)
        provider_events = [event async for event in context.provider.stream(context.provider_request)]
        graph_events = [event for event in provider_events if event.type != "done"]
        update = append_events(state, graph_events)
        update["public_state"] = public_graph_state({**state, **update})
        return update


_CURRENT_CONTEXT: GraphRuntimeContext | None = None


def bind_runtime_context(context: GraphRuntimeContext) -> None:
    global _CURRENT_CONTEXT
    _CURRENT_CONTEXT = context


def clear_runtime_context() -> None:
    global _CURRENT_CONTEXT
    _CURRENT_CONTEXT = None


def _runtime_context(_state: KiraGraphState) -> GraphRuntimeContext:
    if _CURRENT_CONTEXT is None:
        raise RuntimeError("Graph runtime context is not bound")
    return _CURRENT_CONTEXT


def _tool_node(node: WorkflowNodeSpec, dispatcher: ToolNodeDispatcher):
    def invoke_tool(state: KiraGraphState) -> dict[str, Any]:
        if not node.tool_name:
            return append_event(
                state,
                ProviderEvent(
                    type="error",
                    data={"code": "tool_name_missing", "message": "Tool node did not declare a tool name"},
                ),
            )
        arguments = dict(node.tool_args)
        if state.get("project_root") and "root" not in arguments:
            arguments["root"] = state["project_root"]
        context = _runtime_context(state)
        call_index = len(state.get("tool_results", []))
        checkpoint_id = "latest"
        event = dispatcher.invoke(
            node.tool_name,
            arguments,
            thread_id=context.thread_id,
            checkpoint_id=checkpoint_id,
            node_name=node.id,
            call_index=call_index,
            runtime_storage=context.runtime_storage,
        )
        normalized = normalize_graph_events([event])[0]
        start_event = ProviderEvent(
            type="tool_start",
            data={"name": node.tool_name, "node": node.id, "status": "started"},
        )
        update = append_events(state, [start_event, normalized])
        if normalized.type != "error":
            update["tool_results"] = [
                *state.get("tool_results", []),
                {"name": node.tool_name, "result": normalized.data.get("result"), "status": normalized.data.get("status")},
            ]
        return update

    return invoke_tool


def _interrupt_node(node: WorkflowNodeSpec):
    def interrupt_graph(state: KiraGraphState) -> dict[str, Any]:
        payload = _interrupt_payload_for_state(node, state)
        return append_event(state, ProviderEvent(type="interrupt", data=payload))

    return interrupt_graph


def _interrupt_payload_for_state(node: WorkflowNodeSpec, state: KiraGraphState) -> dict[str, Any]:
    payload = dict(node.interrupt_payload or {})
    prompt = (state.get("prompt") or "").lower()
    if payload.get("kind") == "fixture_auto":
        if "python" in prompt:
            return make_interrupt(
                kind="python_approval",
                title="Approve Python execution",
                body="Approve the controlled Python script request.",
                data={"tool_name": "run_python_script", "path": "demo.py"},
            ).public_dict()
        if "edit" in prompt:
            return make_interrupt(
                kind="edit",
                title="Review suggested edit",
                body="Edit the suggested value before the workflow continues.",
                data={"suggested_value": "draft response"},
            ).public_dict()
        if "question" in prompt:
            return make_interrupt(
                kind="question",
                title="Answer required",
                body="Provide the missing answer for the workflow.",
                data={"fields": [{"id": "answer", "label": "Answer", "required": True}]},
            ).public_dict()
        return make_interrupt(
            kind="approval",
            title="Approve workflow step",
            body="Approve this deterministic Stage 05 fixture step.",
            data={"action": "fixture_approval"},
        ).public_dict()
    return make_interrupt(
        kind=payload.get("kind", "approval"),
        title=payload.get("title", "Approve workflow step"),
        body=payload.get("body", "Approve this workflow step."),
        data=payload.get("data") or {},
        metadata=payload.get("metadata") or {},
    ).public_dict()


def _passthrough_node(state: KiraGraphState) -> dict[str, Any]:
    return {"public_state": public_graph_state(state)}


def _condition(name: str):
    if name == "always_tool":
        return lambda _state: "tool"
    if name == "always_end":
        return lambda _state: "end"
    if name == "tool_if_requested":
        return _tool_if_requested
    raise WorkflowValidationError(
        "workflow_validation_error",
        "Unsupported condition",
        [{"code": "unsupported_condition", "condition": name}],
    )


def _tool_if_requested(state: KiraGraphState) -> str:
    if state.get("errors"):
        return "end"
    prompt = (state.get("prompt") or "").lower()
    return "tool" if any(token in prompt for token in ("tool", "file", "project")) else "end"


def _target(name: str) -> str:
    return END if name == END_NODE else name


def failure_class_for_events(events: list[ProviderEvent]) -> FailureClass | None:
    for event in events:
        if event.type == "error":
            return classify_error_code(str(event.data.get("code") or ""))
    return None
