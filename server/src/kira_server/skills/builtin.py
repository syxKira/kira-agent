from __future__ import annotations

from kira_server.graph_runtime.specs import (
    ConditionalEdgeSpec,
    END_NODE,
    NodeMetadata,
    WorkflowEdgeSpec,
    WorkflowNodeSpec,
    WorkflowSpec,
)
from kira_server.skills.packages import SkillPackageLoader
from kira_server.skills.registry import SkillDefinition, SkillRegistry

TEST_SKILL_ID = "stage-03-test-skill"
HITL_FIXTURE_SKILL_ID = "stage-05-hitl-fixture-skill"


def create_builtin_skill_registry(include_test_skill: bool = True, discover_packages: bool = True) -> SkillRegistry:
    registry = SkillRegistry()
    if include_test_skill:
        registry.register(create_stage03_test_skill())
        registry.register(create_stage05_hitl_fixture_skill())
    if discover_packages:
        for package in SkillPackageLoader().discover(include_body=False):
            registry.register_package(package)
    return registry


def create_stage03_test_skill() -> SkillDefinition:
    workflow = WorkflowSpec(
        name="generic-stage-03-workflow",
        description="Generic Stage 03 workflow with one model node and one optional tool node.",
        entrypoint="model_step",
        tools=["list_project_files"],
        nodes=[
            WorkflowNodeSpec(
                id="model_step",
                node_type="model",
                metadata=NodeMetadata(
                    node_type="model",
                    timeout_hint=30,
                    retry_hint=0,
                    side_effect_hint="none",
                    uses_model=True,
                ),
            ),
            WorkflowNodeSpec(
                id="tool_step",
                node_type="tool",
                tool_name="list_project_files",
                tool_args={"limit": 1},
                metadata=NodeMetadata(
                    node_type="tool",
                    allowed_tools=["list_project_files"],
                    timeout_hint=5,
                    retry_hint=0,
                    side_effect_hint="read_only",
                    uses_model=False,
                ),
            ),
        ],
        conditional_edges=[
            ConditionalEdgeSpec(
                source="model_step",
                condition="tool_if_requested",
                routes={"tool": "tool_step", "end": END_NODE},
            )
        ],
        edges=[WorkflowEdgeSpec(source="tool_step", target=END_NODE)],
    )
    return SkillDefinition(
        skill_id=TEST_SKILL_ID,
        name="Stage 03 Test Skill",
        description="A generic workflow used to verify LangGraph runtime integration.",
        workflows=[workflow],
        internal=True,
    )


def create_stage05_hitl_fixture_skill() -> SkillDefinition:
    workflow = WorkflowSpec(
        name="stage-05-hitl-fixture-workflow",
        description="Deterministic Stage 05 workflow that pauses for approval, edit, question, or Python approval.",
        entrypoint="interrupt_step",
        tools=["ask_user_question", "run_python_script"],
        nodes=[
            WorkflowNodeSpec(
                id="interrupt_step",
                node_type="interrupt",
                interrupt_payload={"kind": "fixture_auto"},
                metadata=NodeMetadata(
                    node_type="interrupt",
                    allowed_tools=["ask_user_question", "run_python_script"],
                    timeout_hint=30,
                    retry_hint=0,
                    side_effect_hint="none",
                    uses_model=False,
                ),
            )
        ],
        edges=[WorkflowEdgeSpec(source="interrupt_step", target=END_NODE)],
    )
    return SkillDefinition(
        skill_id=HITL_FIXTURE_SKILL_ID,
        name="Stage 05 HITL Fixture Skill",
        description="A deterministic workflow used to verify interrupt/resume and HITL timeline behavior.",
        workflows=[workflow],
        internal=True,
    )
