from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel

from kira_server.core.events import ProviderEvent
from kira_server.providers.config import ProviderConfig


class ProviderRequest(BaseModel):
    prompt: str
    fixture: str | None = None
    model: str | None = None
    provider_metadata: dict | None = None
    config: ProviderConfig | None = None
    context_items: list[dict] | None = None
    # Optional OpenAI-style tools (function-calling). When provided and the
    # provider supports it, they are forwarded to the upstream API as
    # `tools` + `tool_choice=auto` and the parser can emit tool_call events.
    tools: list[dict] | None = None
    # Optional pre-built OpenAI chat messages. When supplied, the provider
    # uses them verbatim instead of building a single user message from
    # `prompt`. This is the contract the default agent loop relies on for
    # multi-turn tool_call -> tool_result -> answer iterations.
    messages: list[dict] | None = None


class StreamProvider(Protocol):
    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        ...
