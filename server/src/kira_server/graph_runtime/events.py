from __future__ import annotations

from typing import Any

from kira_server.core.events import ProviderEvent
from kira_server.graph_runtime.state import KiraGraphState


def event_to_state_payload(event: ProviderEvent) -> dict[str, Any]:
    return event.model_dump()


def state_payload_to_event(payload: dict[str, Any]) -> ProviderEvent:
    return ProviderEvent.model_validate(payload)


def append_event(state: KiraGraphState, event: ProviderEvent) -> dict[str, Any]:
    events = [*state.get("events", []), event_to_state_payload(event)]
    update: dict[str, Any] = {"events": events}
    if event.type == "error":
        update["errors"] = [
            *state.get("errors", []),
            {
                "code": event.data.get("code", "graph_error"),
                "message": event.data.get("message", "Graph execution failed"),
            },
        ]
    if event.type == "interrupt":
        update["pending_interrupt"] = event.data
    return update


def append_events(state: KiraGraphState, events: list[ProviderEvent]) -> dict[str, Any]:
    payloads = [*state.get("events", []), *[event_to_state_payload(event) for event in events]]
    errors = list(state.get("errors", []))
    for event in events:
        if event.type == "error":
            errors.append(
                {
                    "code": event.data.get("code", "graph_error"),
                    "message": event.data.get("message", "Graph execution failed"),
                }
            )
    update: dict[str, Any] = {"events": payloads}
    if errors:
        update["errors"] = errors
    return update


def events_from_state(state: KiraGraphState) -> list[ProviderEvent]:
    return [state_payload_to_event(payload) for payload in state.get("events", [])]
