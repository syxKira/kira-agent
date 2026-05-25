## ADDED Requirements

### Requirement: ToolNode dispatch uses Stage 02 tools

The system SHALL dispatch workflow tool calls through LangGraph `ToolNode` using tools registered by the Stage 02 tool registry.

#### Scenario: Workflow calls allowed read-only file tool

- **WHEN** a workflow node calls an allowlisted Stage 02 project file tool through `ToolNode`
- **THEN** the tool executes with the same validation, path safety, and bounded output behavior as the existing tool API

#### Scenario: Workflow calls controlled Python tool

- **WHEN** a workflow node calls `run_python_script` through `ToolNode`
- **THEN** the tool executes with the same cwd, env, timeout, and output controls as the existing Stage 02 tool

### Requirement: Workflow tool allowlist enforcement

The system SHALL enforce each workflow's declared tool allowlist before graph compilation and during ToolNode dispatch.

#### Scenario: Missing tool is rejected before compilation

- **WHEN** a workflow declares an allowed tool that is not registered
- **THEN** graph compilation fails with a structured tool validation error

#### Scenario: Disallowed tool call fails

- **WHEN** a workflow attempts to call a tool outside its allowlist
- **THEN** the graph run emits a structured error and does not execute the disallowed tool

### Requirement: No custom business tool router

The system SHALL NOT introduce a custom business workflow router for Stage 02 tools when `ToolNode` can dispatch registered `BaseTool` objects.

#### Scenario: ToolNode owns tool dispatch path

- **WHEN** the test skill graph performs its tool call
- **THEN** the call path uses LangGraph `ToolNode` with registered Stage 02 tools rather than a hand-written workflow-specific router

### Requirement: Tool result normalization

The system SHALL normalize ToolNode results into graph state and Kira event payloads without exposing internal tool objects or unbounded raw output.

#### Scenario: Tool result becomes Kira event payload

- **WHEN** a workflow tool call succeeds
- **THEN** the event stream includes a structured payload with tool name, status, and bounded result data

#### Scenario: Tool error becomes structured graph error

- **WHEN** a workflow tool call returns a validation or execution error
- **THEN** the graph run emits a structured error or tool-result payload that preserves the Stage 02 error code and message

### Requirement: Tool safety boundaries are preserved

The system SHALL preserve Stage 02 safety boundaries for project file tools and controlled Python execution when tools are invoked by graph workflows.

#### Scenario: Project file write remains unavailable

- **WHEN** a workflow attempts to request a write, delete, patch, stage, or general shell capability
- **THEN** no registered ToolNode tool provides that capability

#### Scenario: Path escape remains blocked

- **WHEN** a graph-invoked file tool receives a path outside the allowed root
- **THEN** the Stage 02 path safety behavior rejects the request
