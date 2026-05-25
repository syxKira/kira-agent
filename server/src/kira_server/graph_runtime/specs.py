from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

END_NODE = "__end__"
NodeType = Literal["model", "tool", "passthrough", "interrupt"]


class NodeMetadata(BaseModel):
    node_type: NodeType
    allowed_tools: list[str] = Field(default_factory=list)
    timeout_hint: float | None = Field(default=None, gt=0)
    retry_hint: int | None = Field(default=None, ge=0)
    side_effect_hint: Literal["none", "read_only", "external"] = "none"
    uses_model: bool = False


class WorkflowNodeSpec(BaseModel):
    id: str = Field(min_length=1)
    node_type: NodeType
    metadata: NodeMetadata
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    interrupt_payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def metadata_matches_node(self) -> "WorkflowNodeSpec":
        if self.metadata.node_type != self.node_type:
            raise ValueError("node metadata node_type must match node_type")
        if self.node_type == "model" and not self.metadata.uses_model:
            raise ValueError("model nodes must set metadata.uses_model")
        if self.node_type != "model" and self.metadata.uses_model:
            raise ValueError("only model nodes may set metadata.uses_model")
        if self.node_type == "tool" and not self.tool_name:
            raise ValueError("tool nodes must declare tool_name")
        if self.node_type != "tool" and self.tool_name:
            raise ValueError("only tool nodes may declare tool_name")
        if self.node_type != "interrupt" and self.interrupt_payload:
            raise ValueError("only interrupt nodes may declare interrupt_payload")
        return self


class WorkflowEdgeSpec(BaseModel):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)


class ConditionalEdgeSpec(BaseModel):
    source: str = Field(min_length=1)
    condition: Literal["tool_if_requested", "always_tool", "always_end"]
    routes: dict[str, str] = Field(min_length=1)


class WorkflowSpec(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    entrypoint: str = Field(min_length=1)
    nodes: list[WorkflowNodeSpec] = Field(min_length=1)
    edges: list[WorkflowEdgeSpec] = Field(default_factory=list)
    conditional_edges: list[ConditionalEdgeSpec] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)

    @property
    def node_ids(self) -> set[str]:
        return {node.id for node in self.nodes}

    def node(self, node_id: str) -> WorkflowNodeSpec:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)

    def public_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "entrypoint": self.entrypoint,
            "tools": list(self.tools),
            "nodes": [
                {
                    "id": node.id,
                    "node_type": node.node_type,
                    "metadata": node.metadata.model_dump(),
                    "tool_name": node.tool_name,
                    "interrupt_payload": node.interrupt_payload,
                }
                for node in self.nodes
            ],
            "edges": [edge.model_dump() for edge in self.edges],
            "conditional_edges": [edge.model_dump() for edge in self.conditional_edges],
        }
