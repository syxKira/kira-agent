from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


KiraEventType = Literal[
    "text_delta",
    "thinking_delta",
    "tool_call",
    "tool_start",
    "tool_result",
    "retry",
    "side_effect_reused",
    "checkpoint",
    "interrupt",
    "resume",
    "done",
    "error",
]


class ProviderEvent(BaseModel):
    type: KiraEventType
    data: dict[str, Any] = Field(default_factory=dict)


class KiraEvent(BaseModel):
    type: KiraEventType
    thread_id: str
    seq: int = Field(ge=1)
    data: dict[str, Any] = Field(default_factory=dict)


def normalize_provider_events(thread_id: str, events: list[ProviderEvent]) -> list[KiraEvent]:
    return [
        KiraEvent(
            type=event.type,
            thread_id=thread_id,
            seq=index,
            data={**event.data, "timestamp": _utc_now()},
        )
        for index, event in enumerate(events, start=1)
    ]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
