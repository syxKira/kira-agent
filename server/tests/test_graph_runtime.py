from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from kira_server.core.events import ProviderEvent
from kira_server.graph_runtime.runtime import GraphRuntime, GraphRuntimeContext
from kira_server.graph_runtime.specs import (
    ConditionalEdgeSpec,
    END_NODE,
    NodeMetadata,
    WorkflowEdgeSpec,
    WorkflowNodeSpec,
    WorkflowSpec,
)
from kira_server.graph_runtime.toolnode import create_toolnode_dispatcher
from kira_server.graph_runtime.validation import WorkflowValidationError, validate_workflow
from kira_server.providers.base import ProviderRequest
from kira_server.tooling.registry import create_tool_registry


class FakeProvider:
    def __init__(self, events: list[ProviderEvent] | None = None) -> None:
        self.events = events or [
            ProviderEvent(type="thinking_delta", data={"text": "hidden"}),
            ProviderEvent(type="text_delta", data={"text": "visible"}),
            ProviderEvent(type="done", data={"message": "provider done"}),
        ]
        self.requests: list[ProviderRequest] = []

    async def stream(self, request: ProviderRequest) -> AsyncIterator[ProviderEvent]:
        self.requests.append(request)
        for event in self.events:
            yield event


def test_valid_workflow_spec_passes_validation(tmp_path: Path) -> None:
    workflow = workflow_spec(condition="always_end")
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)

    validate_workflow(workflow, registered_tools=set(registry.tool_names))

    assert workflow.node("model_step").metadata.uses_model is True
    assert workflow.node("tool_step").metadata.side_effect_hint == "read_only"


def test_workflow_validation_rejects_invalid_edges_and_missing_entrypoint(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)
    bad = workflow_spec(condition="always_end").model_copy(
        update={
            "entrypoint": "missing",
            "edges": [WorkflowEdgeSpec(source="tool_step", target="missing")],
        }
    )

    with pytest.raises(WorkflowValidationError) as exc:
        validate_workflow(bad, registered_tools=set(registry.tool_names))

    codes = {error["code"] for error in exc.value.errors}
    assert "missing_entrypoint" in codes
    assert "invalid_edge_target" in codes


def test_workflow_validation_rejects_duplicate_nodes_and_missing_tools(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)
    duplicate = WorkflowSpec(
        name="bad",
        entrypoint="same",
        tools=["missing_tool"],
        nodes=[
            WorkflowNodeSpec(
                id="same",
                node_type="tool",
                tool_name="missing_tool",
                metadata=NodeMetadata(node_type="tool", allowed_tools=["missing_tool"]),
            ),
            WorkflowNodeSpec(
                id="same",
                node_type="tool",
                tool_name="missing_tool",
                metadata=NodeMetadata(node_type="tool", allowed_tools=["missing_tool"]),
            ),
        ],
    )

    with pytest.raises(WorkflowValidationError) as exc:
        validate_workflow(duplicate, registered_tools=set(registry.tool_names))

    codes = {error["code"] for error in exc.value.errors}
    assert "duplicate_node" in codes
    assert "tool_not_registered" in codes


def test_unsupported_node_metadata_is_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkflowNodeSpec(
            id="bad",
            node_type="model",
            metadata=NodeMetadata(node_type="model", uses_model=False),
        )


def test_graph_runtime_model_only_branch_uses_stategraph_and_single_done(tmp_path: Path) -> None:
    provider = FakeProvider()
    events = asyncio.run(run_workflow(workflow_spec(condition="always_end"), tmp_path, provider, "plain request"))

    assert [event.type for event in events] == ["thinking_delta", "text_delta", "done"]
    assert events[0].data["text"] == "hidden"
    assert events[1].data["text"] == "visible"
    assert events[-1].data["message"] == "Graph run completed"
    assert provider.requests[0].provider_metadata["mode"] == "fixture"


def test_graph_runtime_conditional_tool_branch_dispatches_toolnode(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    events = asyncio.run(run_workflow(workflow_spec(condition="tool_if_requested"), tmp_path, FakeProvider(), "use project tool"))

    tool_events = [event for event in events if event.type == "tool_result"]

    assert tool_events
    assert tool_events[0].data["name"] == "list_project_files"
    assert tool_events[0].data["status"] == "ok"
    assert "README.md" in json.dumps(tool_events[0].data["result"])
    assert any(event.type == "tool_start" for event in events)
    assert events[-1].type == "done"


def test_graph_runtime_provider_failure_maps_to_error(tmp_path: Path) -> None:
    provider = FakeProvider([ProviderEvent(type="error", data={"code": "provider_timeout", "message": "timeout"})])

    events = asyncio.run(run_workflow(workflow_spec(condition="always_end"), tmp_path, provider, "hello"))

    assert [event.type for event in events] == ["error"]
    assert events[0].data["code"] == "provider_timeout"


def test_toolnode_rejects_disallowed_tool_without_execution(tmp_path: Path) -> None:
    dispatcher = create_toolnode_dispatcher(create_tool_registry(default_root=tmp_path, prefer_rg=False), ["list_project_files"])

    event = dispatcher.invoke("read_project_file", {"path": "README.md"})

    assert event.type == "error"
    assert event.data["code"] == "tool_not_allowlisted"


def test_toolnode_preserves_path_safety(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    registry = create_tool_registry(default_root=project, prefer_rg=False)
    dispatcher = create_toolnode_dispatcher(registry, ["read_project_file"])

    event = dispatcher.invoke("read_project_file", {"path": "../outside.txt"})

    assert event.type == "error"
    assert event.data["code"] == "path_outside_root"


def test_toolnode_dispatches_controlled_python(tmp_path: Path) -> None:
    script = tmp_path / "ok.py"
    script.write_text("print('ok')", encoding="utf-8")
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)
    dispatcher = create_toolnode_dispatcher(registry, ["run_python_script"])

    event = dispatcher.invoke("run_python_script", {"path": "ok.py"})

    assert event.type == "text_delta"
    assert event.data["name"] == "run_python_script"
    assert event.data["result"]["ok"] is True
    assert event.data["result"]["data"]["stdout"].strip() == "ok"


def test_missing_tool_rejected_before_toolnode_creation(tmp_path: Path) -> None:
    with pytest.raises(WorkflowValidationError) as exc:
        create_toolnode_dispatcher(create_tool_registry(default_root=tmp_path, prefer_rg=False), ["missing_tool"])

    assert exc.value.code == "tool_validation_error"


def test_no_mutation_tools_available_to_graph(tmp_path: Path) -> None:
    registry = create_tool_registry(default_root=tmp_path, prefer_rg=False)
    forbidden_terms = ["write", "delete", "patch", "stage", "git"]

    assert all(not any(term in name for term in forbidden_terms) for name in registry.tool_names)
    assert "run_shell_command" in registry.tool_names


def test_stage03_runtime_creates_no_persistence_artifacts(tmp_path: Path) -> None:
    events = asyncio.run(run_workflow(workflow_spec(condition="always_end"), tmp_path, FakeProvider(), "hello"))

    assert not any(event.type == "checkpoint" for event in events)
    assert not list(tmp_path.glob("*.sqlite"))
    assert not list(tmp_path.glob("*.db"))


async def run_workflow(workflow: WorkflowSpec, root: Path, provider: FakeProvider, prompt: str) -> list[ProviderEvent]:
    runtime = GraphRuntime(create_tool_registry(default_root=root, prefer_rg=False))
    return await runtime.run(
        GraphRuntimeContext(
            prompt=prompt,
            thread_id="local-test",
            skill_id="skill-test",
            workflow=workflow,
            project_root=str(root),
            provider=provider,
            provider_request=ProviderRequest(
                prompt=prompt,
                fixture="welcome",
                model="model-a",
                provider_metadata={"mode": "fixture", "fixture": "welcome"},
            ),
            provider_metadata={"mode": "fixture", "fixture": "welcome"},
        )
    )


def workflow_spec(condition: str) -> WorkflowSpec:
    return WorkflowSpec(
        name="test-workflow",
        entrypoint="model_step",
        tools=["list_project_files"],
        nodes=[
            WorkflowNodeSpec(
                id="model_step",
                node_type="model",
                metadata=NodeMetadata(node_type="model", uses_model=True, retry_hint=0, side_effect_hint="none"),
            ),
            WorkflowNodeSpec(
                id="tool_step",
                node_type="tool",
                tool_name="list_project_files",
                tool_args={"limit": 5},
                metadata=NodeMetadata(
                    node_type="tool",
                    allowed_tools=["list_project_files"],
                    retry_hint=0,
                    side_effect_hint="read_only",
                ),
            ),
        ],
        conditional_edges=[
            ConditionalEdgeSpec(
                source="model_step",
                condition=condition,
                routes={"tool": "tool_step", "end": END_NODE},
            )
        ],
        edges=[WorkflowEdgeSpec(source="tool_step", target=END_NODE)],
    )
