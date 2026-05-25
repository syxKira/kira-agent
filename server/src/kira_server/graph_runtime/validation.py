from __future__ import annotations

from typing import Any

from kira_server.graph_runtime.specs import END_NODE, WorkflowSpec


class WorkflowValidationError(Exception):
    def __init__(self, code: str, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.errors = errors or []

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "errors": self.errors}


def validate_workflow(workflow: WorkflowSpec, *, registered_tools: set[str] | None = None) -> None:
    errors: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    for node in workflow.nodes:
        if node.id in node_ids:
            errors.append({"code": "duplicate_node", "node": node.id})
        node_ids.add(node.id)

    if workflow.entrypoint not in node_ids:
        errors.append({"code": "missing_entrypoint", "entrypoint": workflow.entrypoint})

    for edge in workflow.edges:
        if edge.source not in node_ids:
            errors.append({"code": "invalid_edge_source", "source": edge.source})
        if edge.target != END_NODE and edge.target not in node_ids:
            errors.append({"code": "invalid_edge_target", "target": edge.target})

    for edge in workflow.conditional_edges:
        if edge.source not in node_ids:
            errors.append({"code": "invalid_conditional_source", "source": edge.source})
        if not edge.routes:
            errors.append({"code": "missing_conditional_routes", "source": edge.source})
        for route, target in edge.routes.items():
            if target != END_NODE and target not in node_ids:
                errors.append({"code": "invalid_conditional_target", "route": route, "target": target})

    declared_tools = set(workflow.tools)
    if registered_tools is not None:
        for tool in sorted(declared_tools - registered_tools):
            errors.append({"code": "tool_not_registered", "tool": tool})

    for node in workflow.nodes:
        for tool in node.metadata.allowed_tools:
            if tool not in declared_tools:
                errors.append({"code": "tool_not_allowlisted", "node": node.id, "tool": tool})
            if registered_tools is not None and tool not in registered_tools:
                errors.append({"code": "tool_not_registered", "node": node.id, "tool": tool})
        if node.tool_name:
            if node.tool_name not in declared_tools:
                errors.append({"code": "tool_not_allowlisted", "node": node.id, "tool": node.tool_name})
            if registered_tools is not None and node.tool_name not in registered_tools:
                errors.append({"code": "tool_not_registered", "node": node.id, "tool": node.tool_name})

    if errors:
        raise WorkflowValidationError(
            "workflow_validation_error",
            "Workflow validation failed",
            errors,
        )
