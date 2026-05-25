from __future__ import annotations

from typing import Any

from kira_server.core.events import ProviderEvent
from kira_server.graph_runtime.hitl import validate_interrupt_payload
from kira_server.providers.config import redact_text


def normalize_graph_event(event: ProviderEvent) -> ProviderEvent:
    data = _redact_data(event.data)
    kind = data.get("kind")
    if event.type == "text_delta" and kind == "graph_tool_result":
        return ProviderEvent(type="tool_result", data={key: value for key, value in data.items() if key != "kind"})
    if event.type == "text_delta" and kind == "side_effect_reused":
        return ProviderEvent(type="side_effect_reused", data={key: value for key, value in data.items() if key != "kind"})
    if event.type == "interrupt":
        return ProviderEvent(type="interrupt", data=validate_interrupt_payload(data).public_dict())
    return ProviderEvent(type=event.type, data=data)


def normalize_graph_events(events: list[ProviderEvent]) -> list[ProviderEvent]:
    return [normalize_graph_event(event) for event in events]


def map_langgraph_event(raw: dict[str, Any]) -> ProviderEvent | None:
    name = str(raw.get("event") or "")
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    if name in {"on_chat_model_stream", "on_llm_stream"}:
        chunk = data.get("chunk") or {}
        text = _chunk_text(chunk)
        if text:
            return ProviderEvent(type="text_delta", data={"text": text})
        return None
    if name in {"on_tool_start"}:
        return ProviderEvent(type="tool_start", data={"name": data.get("name") or raw.get("name") or "tool"})
    if name in {"on_tool_end"}:
        return ProviderEvent(type="tool_result", data={"name": data.get("name") or raw.get("name") or "tool", "result": data.get("output")})
    if name in {"on_chain_end", "on_graph_end"}:
        return ProviderEvent(type="done", data={"message": "Graph run completed"})
    if name in {"on_chain_error", "on_tool_error"}:
        return ProviderEvent(type="error", data={"code": "graph_runtime_error", "message": redact_text(str(data.get("error") or "Graph execution failed"))})
    return None


def _chunk_text(chunk: Any) -> str:
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, dict):
        content = chunk.get("content")
        return content if isinstance(content, str) else ""
    content = getattr(chunk, "content", "")
    return content if isinstance(content, str) else ""


def _redact_data(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in {"api_key", "apikey", "authorization"}:
            continue
        if isinstance(value, str):
            result[key] = redact_text(value)
        elif isinstance(value, dict):
            result[key] = _redact_data(value)
        elif isinstance(value, list):
            result[key] = [_redact_value(item) for item in value]
        else:
            result[key] = value
    return result


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return _redact_data(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value
