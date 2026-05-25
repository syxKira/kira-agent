from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import httpx
import pytest

from kira_server.providers.base import ProviderRequest
from kira_server.providers.config import ProviderConfig, RetryConfig, load_provider_config
from kira_server.providers.openai_compatible import (
    OpenAICompatibleProvider,
    ProviderStreamError,
    collect_openai_stream_events,
)


def test_stream_parser_maps_visible_reasoning_and_completion() -> None:
    events = asyncio.run(
        collect_openai_stream_events(
            _lines(
                'data: {"choices":[{"delta":{"reasoning_content":"hidden "}}]}',
                'data: {"choices":[{"delta":{"content":"visible"}}]}',
                "data: [DONE]",
            )
        )
    )

    assert [event.type for event in events] == ["thinking_delta", "text_delta", "done"]
    assert events[0].data["text"] == "hidden "
    assert events[1].data["text"] == "visible"


def test_stream_parser_keeps_think_tags_out_of_visible_text_across_chunks() -> None:
    events = asyncio.run(
        collect_openai_stream_events(
            _lines(
                'data: {"choices":[{"delta":{"content":"visible <thi"}}]}',
                'data: {"choices":[{"delta":{"content":"nk>hidden</th"}}]}',
                'data: {"choices":[{"delta":{"content":"ink> answer"}}]}',
                "data: [DONE]",
            )
        )
    )

    visible_text = "".join(event.data.get("text", "") for event in events if event.type == "text_delta")
    thinking_text = "".join(event.data.get("text", "") for event in events if event.type == "thinking_delta")

    assert visible_text == "visible  answer"
    assert thinking_text == "hidden"


def test_stream_parser_rejects_malformed_payloads() -> None:
    with pytest.raises(ProviderStreamError) as exc:
        asyncio.run(collect_openai_stream_events(_lines("data: {not-json")))

    assert exc.value.code == "provider_parse_error"


def test_openai_provider_streams_successful_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://provider.test/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer sk-test-secret"
        return httpx.Response(
            200,
            text='data: {"choices":[{"delta":{"content":"hello"}}]}\n\ndata: [DONE]\n\n',
            headers={"content-type": "text/event-stream"},
        )

    events = asyncio.run(_stream_with_handler(handler))

    assert [event.type for event in events] == ["text_delta", "done"]
    assert events[0].data["text"] == "hello"


def test_openai_provider_maps_non_2xx_to_structured_error() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="bad api key sk-test-secret")

    events = asyncio.run(_stream_with_handler(handler))

    assert [event.type for event in events] == ["error"]
    assert events[0].data["code"] == "provider_http_error"
    assert events[0].data["metadata"]["status_code"] == 401
    assert "sk-test-secret" not in str(events[0].data)


def test_openai_provider_maps_timeout_to_structured_error() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("request timed out")

    events = asyncio.run(_stream_with_handler(handler))

    assert [event.type for event in events] == ["error"]
    assert events[0].data["code"] == "provider_timeout"


def test_openai_provider_reports_retry_exhaustion() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, text="unavailable")

    events = asyncio.run(_stream_with_handler(handler, retry=RetryConfig(attempts=1, backoff_seconds=0)))

    assert calls == 2
    assert [event.type for event in events] == ["error"]
    assert events[0].data["code"] == "provider_retry_exhausted"
    assert events[0].data["metadata"]["last_code"] == "provider_http_error"


def test_openai_provider_maps_malformed_stream_to_structured_error() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="data: {not-json\n\n")

    events = asyncio.run(_stream_with_handler(handler))

    assert [event.type for event in events] == ["error"]
    assert events[0].data["code"] == "provider_parse_error"


@pytest.mark.skipif(os.environ.get("KIRA_REAL_LLM_SMOKE") != "1", reason="real LLM smoke test is opt-in")
def test_real_llm_provider_smoke_is_opt_in() -> None:
    store = load_provider_config()
    config = store.get(None)
    if config is None or not config.has_api_key:
        pytest.skip("KIRA_REAL_LLM_SMOKE=1 requires a configured provider with an API key")

    events = asyncio.run(_stream_real(config))

    assert any(event.type in {"text_delta", "done"} for event in events)
    assert not any(event.type == "error" for event in events)


async def _stream_real(config: ProviderConfig) -> list:
    provider = OpenAICompatibleProvider()
    events = []
    async for event in provider.stream(ProviderRequest(prompt="Reply with the word pong.", config=config)):
        events.append(event)
    return events


async def _stream_with_handler(
    handler,
    *,
    retry: RetryConfig | None = None,
) -> list:
    config = ProviderConfig(
        name="test",
        base_url="https://provider.test/v1",
        model="model-a",
        api_key="sk-test-secret",
        retry=retry or RetryConfig(attempts=0),
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleProvider(client=client)
        events = []
        async for event in provider.stream(ProviderRequest(prompt="hello", config=config)):
            events.append(event)
        return events


async def _lines(*values: str) -> AsyncIterator[str]:
    for value in values:
        yield value
