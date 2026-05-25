from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from kira_server.core.events import ProviderEvent
from kira_server.providers.base import ProviderRequest


FIXTURE_SCRIPTS: dict[str, list[ProviderEvent]] = {
    "welcome": [
        ProviderEvent(type="thinking_delta", data={"text": "Preparing local fixture run"}),
        ProviderEvent(
            type="text_delta",
            data={
                "kind": "fixture_tool_result",
                "name": "welcome_fixture",
                "result": {"status": "ok", "message": "Fixture event stream ready"},
            },
        ),
        ProviderEvent(type="text_delta", data={"text": "Kira local fixture is running."}),
        ProviderEvent(type="text_delta", data={"text": " The Stage 01 web loop is ready."}),
        ProviderEvent(type="done", data={"message": "Fixture run completed"}),
    ],
    "error": [
        ProviderEvent(type="thinking_delta", data={"text": "Preparing error fixture"}),
        ProviderEvent(type="error", data={"message": "Fixture error for failure-state testing"}),
    ],
}


class FixtureProvider:
    def __init__(self, delay_seconds: float = 0.05) -> None:
        self._delay_seconds = delay_seconds

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        fixture = request.fixture or "welcome"
        events = FIXTURE_SCRIPTS.get(fixture, _default_events(fixture))
        for event in events:
            if self._delay_seconds > 0:
                await asyncio.sleep(self._delay_seconds)
            yield event


def _default_events(fixture: str) -> list[ProviderEvent]:
    return [
        ProviderEvent(type="text_delta", data={"text": f"No fixture named '{fixture}' was found."}),
        ProviderEvent(type="done", data={"message": "Fallback fixture completed"}),
    ]
