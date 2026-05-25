"""Tests for the default agent loop (no-skill code path).

Covers:
* Multi-turn tool_call -> tool_result -> final answer pipelining.
* Surface of tool_start / tool_result events without forwarding the
  internal ``tool_call`` provider event.
* Reject path when the model requests a tool that is not allow-listed.
* Iteration cap producing a deterministic terminal ``done`` event.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

from kira_server.core.events import ProviderEvent
from kira_server.graph_runtime.agent_loop import build_default_system_prompt, run_default_agent
from kira_server.providers.base import ProviderRequest
from kira_server.tooling.registry import ToolRegistry


class ScriptedProvider:
    """Provider stub that yields a different scripted stream per call."""

    def __init__(self, scripts: list[list[ProviderEvent]]) -> None:
        self._scripts = list(scripts)
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        events = self._scripts.pop(0) if self._scripts else [
            ProviderEvent(type="done", data={"message": "out_of_script"})
        ]
        for event in events:
            yield event


async def _collect(agen: AsyncIterator[ProviderEvent]) -> list[ProviderEvent]:
    return [event async for event in agen]


def _run_agent(**kwargs) -> list[ProviderEvent]:
    return asyncio.run(_collect(run_default_agent(**kwargs)))


def _base_request() -> ProviderRequest:
    return ProviderRequest(prompt="ignored", model="model-a")


def test_default_system_prompt_encourages_on_demand_project_lookup() -> None:
    prompt = build_default_system_prompt(
        tool_names=["search_project_files", "read_project_file"],
        has_skills=False,
    )

    assert "search or read project files only when the user's task needs local project facts" in prompt
    assert "prefer search_project_files" in prompt
    assert "use that exact installed path" in prompt
    assert "do not mix fields or commands from unrelated variants" in prompt
    assert "preserve literal template defaults" in prompt
    assert "generated data exactly once in one code block" in prompt
    assert "make the first shell call the target script" in prompt
    assert "including python -c" in prompt
    assert "minified single-line JSON" in prompt
    assert "separators=(',', ':')" in prompt
    assert "satisfy them literally" in prompt
    assert "do not inspect .env files" in prompt
    assert "Never ask the user to paste secret values into chat" in prompt
    assert "do not suggest using --token with a pasted secret" in prompt


def test_agent_loop_runs_tool_call_then_final_answer(tmp_path: Path) -> None:
    # Prepare a tiny project so list_project_files returns something.
    (tmp_path / "alpha.txt").write_text("alpha\n", encoding="utf-8")
    registry = ToolRegistry(default_root=tmp_path)

    scripts = [
        # First turn: model asks the tool.
        [
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-1",
                    "name": "list_project_files",
                    "arguments_json": json.dumps({"limit": 5}),
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={"message": "calling tool"}),
        ],
        # Second turn: model produces the final answer.
        [
            ProviderEvent(type="text_delta", data={"text": "I found one file."}),
            ProviderEvent(type="done", data={"message": "ok"}),
        ],
    ]
    provider = ScriptedProvider(scripts)

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["list_project_files"],
        system_prompt=build_default_system_prompt(
            tool_names=["list_project_files"], has_skills=False
        ),
        context_items=None,
        user_message="please list",
    )

    types = [event.type for event in events]
    # The internal tool_call must not surface; only the lifecycle events
    # plus the final visible/text/done turn must.
    assert types == ["tool_start", "tool_result", "text_delta", "done"]

    # Two provider streams: one for the tool call, one for the answer.
    assert len(provider.requests) == 2
    second_messages = provider.requests[1].messages or []
    roles = [message.get("role") for message in second_messages]
    # Loop must replay the assistant tool_calls turn and the tool reply.
    assert "assistant" in roles
    assert "tool" in roles
    tool_message = next(message for message in second_messages if message.get("role") == "tool")
    assert tool_message["tool_call_id"] == "call-1"


def test_agent_loop_disables_tools_after_missing_credential(tmp_path: Path) -> None:
    registry = ToolRegistry(default_root=tmp_path)
    scripts = [
        [
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-token",
                    "name": "run_shell_command",
                    "arguments_json": json.dumps(
                        {
                            "command": "printf 'Missing token. Set DS_TOKEN or pass --token.\\n' >&2; exit 1",
                            "timeout_seconds": 2,
                        }
                    ),
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={"message": "calling tool"}),
        ],
    ]
    provider = ScriptedProvider(scripts)

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["run_shell_command"],
        system_prompt="system",
        context_items=None,
        user_message="send data",
    )

    assert [event.type for event in events] == ["tool_start", "tool_result", "text_delta", "done"]
    assert provider.requests[0].tools
    assert len(provider.requests) == 1
    visible = "".join(event.data.get("text", "") for event in events if event.type == "text_delta")
    assert "DS_TOKEN" in visible
    assert "--token" not in visible
    assert "paste your" not in visible.lower()
    assert "send me" not in visible.lower()


def test_agent_loop_missing_credential_does_not_repeat_existing_code_block(tmp_path: Path) -> None:
    registry = ToolRegistry(default_root=tmp_path)
    (tmp_path / "send.py").write_text(
        "import sys\nprint('Missing token. Set DS_TOKEN or pass --token.', file=sys.stderr)\nsys.exit(1)\n",
        encoding="utf-8",
    )
    payload = {"data": {"#name": "ad_tracker"}}
    scripts = [
        [
            ProviderEvent(type="text_delta", data={"text": "```json\n{\"data\":{\"#name\":\"ad_tracker\"}}\n```\n"}),
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-token",
                    "name": "run_shell_command",
                    "arguments_json": json.dumps(
                        {
                            "command": (
                                "python send.py "
                                f"--json '{json.dumps(payload, separators=(',', ':'))}' --wait"
                            ),
                            "timeout_seconds": 2,
                        }
                    ),
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={"message": "calling tool"}),
        ],
    ]
    provider = ScriptedProvider(scripts)

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["run_shell_command"],
        system_prompt="system",
        context_items=None,
        user_message="帮我造一条adtracker广告数据，数据压缩成一行在单独的一个代码块里输出，然后发送一下",
    )

    visible = "".join(event.data.get("text", "") for event in events if event.type == "text_delta")
    assert visible.count("```json") == 1
    assert "不要在聊天中粘贴 token" in visible


def test_agent_loop_missing_credential_includes_json_when_model_skipped_display(tmp_path: Path) -> None:
    registry = ToolRegistry(default_root=tmp_path)
    (tmp_path / "send.py").write_text(
        "import sys\nprint('Missing token. Set DS_TOKEN or pass --token.', file=sys.stderr)\nsys.exit(1)\n",
        encoding="utf-8",
    )
    payload = {"data": {"#name": "ad_tracker"}, "ts": 1}
    scripts = [
        [
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-token",
                    "name": "run_shell_command",
                    "arguments_json": json.dumps(
                        {
                            "command": (
                                "python send.py "
                                f"--json '{json.dumps(payload, separators=(',', ':'))}' --wait"
                            ),
                            "timeout_seconds": 2,
                        }
                    ),
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={"message": "calling tool"}),
        ],
    ]
    provider = ScriptedProvider(scripts)

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["run_shell_command"],
        system_prompt="system",
        context_items=None,
        user_message="帮我造一条adtracker广告数据，数据压缩成一行在单独的一个代码块里输出，然后发送一下",
    )

    visible = "".join(event.data.get("text", "") for event in events if event.type == "text_delta")
    assert "```json\n{\"data\":{\"#name\":\"ad_tracker\"},\"ts\":1}\n```" in visible
    assert visible.count("```json") == 1


def test_agent_loop_hides_preliminary_json_synthesis_shell_call(tmp_path: Path) -> None:
    registry = ToolRegistry(default_root=tmp_path)
    (tmp_path / "send.py").write_text(
        "import sys\nprint('Missing token. Set DS_TOKEN or pass --token.', file=sys.stderr)\nsys.exit(1)\n",
        encoding="utf-8",
    )
    payload = {"data": {"#name": "ad_tracker", "match_type": ""}, "ts": 1}
    scripts = [
        [
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-synth",
                    "name": "run_shell_command",
                    "arguments_json": json.dumps(
                        {
                            "command": "python3 -c \"import json; print(json.dumps({'data': {'#name': 'ad_tracker'}}))\"",
                        }
                    ),
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={"message": "calling tool"}),
        ],
        [
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-send",
                    "name": "run_shell_command",
                    "arguments_json": json.dumps(
                        {
                            "command": (
                                "python send.py "
                                f"--json '{json.dumps(payload, separators=(',', ':'))}' --wait"
                            ),
                            "timeout_seconds": 2,
                        }
                    ),
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={"message": "calling tool"}),
        ],
    ]
    provider = ScriptedProvider(scripts)

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["run_shell_command"],
        system_prompt="system",
        context_items=None,
        user_message="帮我造一条adtracker广告数据，数据压缩成一行在单独的一个代码块里输出，然后发送一下",
    )

    tool_starts = [event for event in events if event.type == "tool_start"]
    assert len(tool_starts) == 1
    assert "send.py" in tool_starts[0].data["arguments"]["command"]
    assert "python3 -c" not in tool_starts[0].data["arguments"]["command"]
    visible = "".join(event.data.get("text", "") for event in events if event.type == "text_delta")
    assert "```json\n{\"data\":{\"#name\":\"ad_tracker\",\"match_type\":\"\"},\"ts\":1}\n```" in visible
    assert len(provider.requests) == 2
    assert "json_synthesis_shell_denied" in json.dumps(provider.requests[1].messages, ensure_ascii=False)


def test_agent_loop_blocks_disallowed_tool(tmp_path: Path) -> None:
    registry = ToolRegistry(default_root=tmp_path)

    scripts = [
        [
            ProviderEvent(
                type="tool_call",
                data={
                    "call_id": "call-x",
                    "name": "run_python_script",
                    "arguments_json": "{}",
                    "index": 0,
                },
            ),
            ProviderEvent(type="done", data={}),
        ],
        [
            ProviderEvent(type="text_delta", data={"text": "blocked"}),
            ProviderEvent(type="done", data={}),
        ],
    ]
    provider = ScriptedProvider(scripts)

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["list_project_files"],
        system_prompt="system",
        context_items=None,
        user_message="please",
    )

    tool_results = [event for event in events if event.type == "tool_result"]
    assert len(tool_results) == 1
    assert tool_results[0].data["status"] == "error"
    assert tool_results[0].data["result"]["code"] == "tool_not_allowlisted"


def test_agent_loop_emits_terminal_done_when_max_iterations_reached(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("alpha\n", encoding="utf-8")
    registry = ToolRegistry(default_root=tmp_path)

    # Always reply with the same tool_call so the loop never converges.
    repeating = [
        ProviderEvent(
            type="tool_call",
            data={
                "call_id": "call-loop",
                "name": "list_project_files",
                "arguments_json": "{}",
                "index": 0,
            },
        ),
        ProviderEvent(type="done", data={}),
    ]
    provider = ScriptedProvider([list(repeating) for _ in range(5)])

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=registry,
        allowed_tools=["list_project_files"],
        system_prompt="system",
        context_items=None,
        user_message="please",
        max_iterations=2,
    )

    assert events[-1].type == "done"
    assert events[-1].data.get("max_iterations") == 2


def test_agent_loop_passes_through_text_only_responses() -> None:
    provider = ScriptedProvider(
        [
            [
                ProviderEvent(type="thinking_delta", data={"text": "hidden"}),
                ProviderEvent(type="text_delta", data={"text": "hello"}),
                ProviderEvent(type="done", data={"message": "ok"}),
            ]
        ]
    )

    events = _run_agent(
        provider=provider,
        base_request=_base_request(),
        tool_registry=ToolRegistry(),
        allowed_tools=[],
        system_prompt="system",
        context_items=None,
        user_message="hi",
    )

    assert [event.type for event in events] == ["thinking_delta", "text_delta", "done"]
    # No tools were enabled; the provider must not see a ``tools`` field.
    assert provider.requests[0].tools is None
