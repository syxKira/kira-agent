## Why

Stage 01 proves the local web loop, but Kira cannot safely add LangGraph `ToolNode` dispatch until built-in tools have stable schemas, validation, result envelopes, and local boundary rules. Stage 02 introduces the first tool layer and safe local context primitives while deliberately avoiding graph execution, retrieval indexing, checkpointing, memory, or write-capable tools.

## What Changes

- Add a LangChain Core-only tool protocol layer using `BaseTool` / `@tool` compatible schemas.
- Add a backend tool registry that exposes built-in tool metadata and JSON Schema through `GET /api/tools`.
- Add normalized `ToolResult` handling for success, validation errors, permission errors, timeout errors, execution errors, truncation, and output caps.
- Add read-only local project file tools: `list_project_files`, `search_project_files`, and `read_project_file`.
- Add a project root resolver and ignore policy for traversal, symlink escape, dependency/build/cache directories, binary files, large files, and `.gitignore` where practical.
- Add controlled `run_python_script` execution with bounded cwd, env allowlist, timeout, stdout/stderr caps, no shell expansion, and structured metadata.
- Add `ask_user_question` as a structured human-input request placeholder without Stage 05 interrupt/resume UX.
- Add focused backend tests for tool schema export, validation, local file safety, no-`rg` fallback behavior, binary/large file handling, Python timeout/output caps, and result normalization.
- Defer LangGraph `ToolNode` dispatch, LangChain agents/chains/memory, retrieval indexing/citations/ContextItem packing, frontend HITL approval UX, persistent audit storage, and file mutation tools.

## Capabilities

### New Capabilities

- `tool-registry-schema`: Built-in LangChain Core tool registry, schema export, and normalized tool result contract.
- `project-file-tools`: Read-only project file listing, search, and bounded read tools with root/ignore/binary/large-file safety rules.
- `controlled-python-execution`: Bounded Python subprocess execution as a tool, with cwd/env/timeout/output controls and no shell semantics.
- `hitl-question-placeholder`: Structured `ask_user_question` tool result shape for future HITL interrupt integration.

### Modified Capabilities

- None.

## Impact

- Affected backend areas: `server/` API routes, tool registry modules, local file policy utilities, and tests.
- Affected shared contracts: `src/` schemas or examples for tool metadata and `ToolResult` shapes if needed by frontend or future graph runtime.
- New API surface: `GET /api/tools`.
- New dependency: `langchain-core` for tool primitives only.
- Stage 02 must preserve the Stage 01 run/SSE behavior and must not add LangGraph, ToolNode dispatch, checkpointing/resume, retrieval index/search APIs, memory, production auth, general shell, or write/edit file tools.
