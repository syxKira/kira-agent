from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from kira_server.core.events import ProviderEvent
from kira_server.graph_runtime.validation import WorkflowValidationError
from kira_server.storage.database import RuntimeStorage
from kira_server.storage.idempotency import args_hash, idempotency_key
from kira_server.tooling.registry import ToolRegistry


class ToolInvocationState(TypedDict):
    messages: list[Any]


class ToolNodeDispatcher:
    def __init__(self, registry: ToolRegistry, allowed_tools: list[str]) -> None:
        self._registry = registry
        self._allowed = set(allowed_tools)
        self._tool_node = ToolNode(registry.tools_for_graph(allowed_tools))

    def invoke(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        thread_id: str | None = None,
        checkpoint_id: str = "latest",
        node_name: str | None = None,
        call_index: int = 0,
        runtime_storage: RuntimeStorage | None = None,
    ) -> ProviderEvent:
        if name not in self._allowed:
            if runtime_storage and thread_id:
                runtime_storage.record_audit(
                    action="tool.dispatch",
                    status="denied",
                    decision="deny",
                    thread_id=thread_id,
                    tool=name,
                    metadata={"allowed_tools": sorted(self._allowed)},
                    summary="Tool dispatch denied by workflow allowlist",
                )
            return ProviderEvent(
                type="error",
                data={
                    "code": "tool_not_allowlisted",
                    "message": f"Tool '{name}' is not allowed for this workflow",
                    "metadata": {"tool": name},
                },
            )
        ledger_key = None
        if runtime_storage and thread_id and node_name:
            ledger_key = idempotency_key(
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                node_name=node_name,
                call_index=call_index,
                tool_name=name,
                arguments=arguments,
            )
            existing = runtime_storage.ledger_get(ledger_key)
            if existing and existing["status"] == "completed":
                runtime_storage.record_audit(
                    action="side_effect.reuse",
                    status="reused",
                    decision="allow",
                    thread_id=thread_id,
                    tool=name,
                    metadata={"idempotency_key": ledger_key, "result": existing.get("result_summary")},
                    summary="Side-effect ledger reused a completed tool result",
                )
                return ProviderEvent(
                    type="text_delta",
                    data={
                        "kind": "side_effect_reused",
                        "name": name,
                        "status": "reused",
                        "idempotency_key": ledger_key,
                        "result": existing.get("result_summary"),
                    },
                )
            if existing and existing["status"] == "unknown":
                runtime_storage.record_audit(
                    action="side_effect.reuse",
                    status="unknown",
                    decision="ask",
                    thread_id=thread_id,
                    tool=name,
                    metadata={"idempotency_key": ledger_key},
                    summary="Side-effect ledger requires repair before reuse",
                )
                return ProviderEvent(
                    type="error",
                    data={
                        "code": "side_effect_unknown",
                        "message": "Side-effect status is unknown and requires repair",
                        "metadata": {"tool": name, "idempotency_key": ledger_key},
                    },
                )
            runtime_storage.ledger_record(
                key=ledger_key,
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                node=node_name,
                tool=name,
                args_hash_value=args_hash(arguments),
                status="started",
            )
            runtime_storage.record_audit(
                action="tool.dispatch",
                status="started",
                decision="allow",
                thread_id=thread_id,
                tool=name,
                metadata={"node": node_name, "idempotency_key": ledger_key, "arguments": arguments},
                summary="Tool dispatch started",
            )

        message = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": name,
                    "args": arguments,
                    "id": f"tool-{uuid4().hex}",
                    "type": "tool_call",
                }
            ],
        )
        graph = StateGraph(ToolInvocationState)
        graph.add_node("tools", self._tool_node)
        graph.set_entry_point("tools")
        graph.add_edge("tools", END)
        result = graph.compile().invoke({"messages": [message]})
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if not messages:
            if runtime_storage and thread_id:
                runtime_storage.record_audit(
                    action="tool.dispatch",
                    status="failed",
                    decision="allow",
                    thread_id=thread_id,
                    tool=name,
                    metadata={"node": node_name, "idempotency_key": ledger_key, "code": "tool_result_missing"},
                    summary="Tool dispatch failed without a result",
                )
            return ProviderEvent(
                type="error",
                data={
                    "code": "tool_result_missing",
                    "message": "ToolNode did not return a tool result",
                    "metadata": {"tool": name},
                },
            )
        parsed = _parse_tool_content(getattr(messages[-1], "content", ""))
        if isinstance(parsed, dict) and parsed.get("ok") is False:
            if runtime_storage and ledger_key and thread_id and node_name:
                runtime_storage.ledger_record(
                    key=ledger_key,
                    thread_id=thread_id,
                    checkpoint_id=checkpoint_id,
                    node=node_name,
                    tool=name,
                    args_hash_value=args_hash(arguments),
                    status="failed",
                    result_summary=parsed,
                )
                runtime_storage.record_audit(
                    action="tool.dispatch",
                    status="failed",
                    decision="allow",
                    thread_id=thread_id,
                    tool=name,
                    metadata={"node": node_name, "idempotency_key": ledger_key, "result": parsed},
                    summary="Tool dispatch failed",
                )
            return ProviderEvent(
                type="error",
                data={
                    "code": parsed.get("code") or "tool_error",
                    "message": parsed.get("message") or "Tool execution failed",
                    "metadata": {"tool": name, "result": parsed},
                },
            )
        if runtime_storage and ledger_key and thread_id and node_name:
            runtime_storage.ledger_record(
                key=ledger_key,
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                node=node_name,
                tool=name,
                args_hash_value=args_hash(arguments),
                status="completed",
                result_summary=parsed,
            )
            runtime_storage.record_audit(
                action="tool.dispatch",
                status="completed",
                decision="allow",
                thread_id=thread_id,
                tool=name,
                metadata={"node": node_name, "idempotency_key": ledger_key, "result": parsed},
                summary="Tool dispatch completed",
            )
        return ProviderEvent(
            type="text_delta",
            data={
                "kind": "graph_tool_result",
                "name": name,
                "status": "ok",
                "idempotency_key": ledger_key,
                "result": parsed,
            },
        )


def create_toolnode_dispatcher(registry: ToolRegistry, allowed_tools: list[str]) -> ToolNodeDispatcher:
    missing = sorted(set(allowed_tools) - set(registry.tool_names))
    if missing:
        raise WorkflowValidationError(
            "tool_validation_error",
            "Workflow declares tools that are not registered",
            [{"code": "tool_not_registered", "tool": name} for name in missing],
        )
    return ToolNodeDispatcher(registry, allowed_tools)


def _parse_tool_content(content: Any) -> Any:
    if isinstance(content, list):
        return [_parse_tool_content(item) for item in content]
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content
