# tool-registry-schema Specification

## Purpose
TBD - created by archiving change stage-02-tool-protocol-local-context. Update Purpose after archive.
## Requirements
### Requirement: Register built-in tools

The system SHALL register Stage 02 built-in tools through a single backend registry using LangChain Core `BaseTool` or `@tool` compatible definitions.

#### Scenario: Registry includes built-in tool names

- **WHEN** the backend initializes the Stage 02 tool registry
- **THEN** it includes `list_project_files`, `search_project_files`, `read_project_file`, `run_python_script`, and `ask_user_question`

### Requirement: Export tool schemas

The system SHALL expose `GET /api/tools` with metadata and JSON Schema for every registered built-in tool.

#### Scenario: API returns tool metadata

- **WHEN** a client calls `GET /api/tools`
- **THEN** the response includes each tool name, description, argument schema, result schema metadata, and read/write risk classification

#### Scenario: Tool schemas are model-dispatch compatible

- **WHEN** a built-in tool is exported through `GET /api/tools`
- **THEN** its argument schema is derived from the same LangChain Core tool definition that future LangGraph `ToolNode` dispatch can consume

### Requirement: Normalize tool results

The system SHALL normalize tool execution outcomes into a stable `ToolResult` envelope.

#### Scenario: Successful tool result

- **WHEN** a tool completes successfully
- **THEN** its result includes `ok: true`, a stable `code`, `data`, `metadata`, and a `truncated` flag

#### Scenario: Failed tool result

- **WHEN** a tool fails validation, permission checks, lookup, timeout, binary checks, size checks, or execution
- **THEN** its result includes `ok: false`, a stable error `code`, a concise `message`, structured `metadata`, and no uncaught traceback in user-facing fields

### Requirement: Preserve Stage 02 boundaries

The system SHALL NOT add LangGraph `ToolNode` dispatch, LangChain agents/chains/memory, checkpointing, resume, or file mutation tools as part of the Stage 02 tool registry.

#### Scenario: Registry excludes later-stage capabilities

- **WHEN** `GET /api/tools` returns registered tools
- **THEN** no tool writes, patches, deletes, stages files, invokes a general shell, dispatches a graph, or manages memory

