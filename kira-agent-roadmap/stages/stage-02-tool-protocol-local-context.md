# Stage 02: Tool Protocol + Local Context

## Goal

Add Kira's first tool layer using only `langchain-core` `@tool` / `BaseTool`: schema-backed tools, argument validation, structured results, project-local read-only file access, `ask_user_question`, and controlled Python script execution.

## Why This Stage

Tools must have stable schemas before LangGraph `ToolNode` can dispatch them. Kira also needs safe local project context early because general agents still need to read nearby project files, documents, fixtures, and configuration. In this stage those capabilities are tools; Stage 06 upgrades them into a retrieval system with an index, chunks, citations, and context packing.

## Scope

- Tool registry exposing `BaseTool` metadata and JSON Schema.
- `GET /api/tools`.
- `list_project_files`, `search_project_files`, `read_project_file`.
- Stable file result metadata that a later retrieval system can index and cite.
- `run_python_script` with controlled execution.
- `ask_user_question` as a structured HITL request placeholder.
- Tool result normalization and output caps.

Excluded:

- File mutation tools.
- General shell.
- LangChain agents/chains/memory.
- ToolNode graph dispatch; that lands in Stage 03.

## Inputs And Dependencies

- Stage 01 backend and event contract.
- `langchain-core`.
- `rg` when available, with Python fallback for listing/search.
- Project root resolver and ignore policy.

## Design

### Tool Protocol

Every built-in tool is a `BaseTool` or `@tool` function with type hints and docstrings sufficient to derive JSON Schema. Kira wraps tool execution to normalize success, validation errors, permission errors, timeouts, and execution errors.

### Local File Tools

Kira inherits Kai's `grep/glob/read` discipline but narrows it into read-only project context. These are primitive access tools, not the whole retrieval system:

| Tool | Behavior |
| --- | --- |
| `list_project_files(root?, glob?, limit?)` | List files under project root, prefer `rg --files`, cap results |
| `search_project_files(query, root?, glob?, limit?)` | Full-text search, prefer `rg`, Python fallback if unavailable |
| `read_project_file(path, offset?, limit?)` | Read bounded text file slices |

Rules:

- Resolve every path inside project root.
- Reject path traversal and symlink escape.
- Ignore `.git`, dependency directories, build outputs, caches, and sensitive hidden directories by default.
- Respect `.gitignore` where practical.
- Reject binary files and oversized reads with structured errors.
- Never write, move, delete, patch, format, or stage files.
- Return stable metadata needed for Stage 06: canonical path, root ID, byte range or line range, file size, mtime, content hash when cheap, truncation status, ignore reason, and error code.
- Convert results into cited `ContextItem(kind="project_file")` or `ContextItem(kind="project_search")` in Stage 06.

Stage 02 should not build an index yet. It defines the safe I/O boundary and result shape so Stage 06 can add inventory, chunking, FTS/lexical retrieval, ranking, citations, stale-source detection, and prompt-injection labeling without changing tool contracts.

### Controlled Python Execution

`run_python_script` accepts a workspace script path or a system-created temporary script reference. It runs through Python subprocess, not a general shell, with timeout, cwd allowlist, env allowlist, output caps, audit metadata, and optional HITL approval for risky actions.

## Implementation Tasks

1. Add tool registry and schema export.
2. Implement structured `ToolResult` normalization.
3. Implement project root resolver and ignore defaults.
4. Implement `list_project_files`.
5. Implement `search_project_files`.
6. Implement `read_project_file`.
7. Implement controlled `run_python_script`.
8. Implement `ask_user_question` result shape.
9. Add path, binary, large-file, no-`rg`, validation, and timeout tests.

## Validation

- `/api/tools` returns JSON Schema for every built-in tool.
- Listing and search work with and without `rg`.
- Path traversal and symlink escape are rejected.
- Large files and binary files return structured errors.
- Python execution times out and truncates output correctly.

## Exit Criteria

- Tool protocol can be consumed by LangGraph `ToolNode`.
- Local project retrieval is useful but strictly read-only.
- Python execution cannot become a general shell by accident.

## Deferred Work

- Tool dispatch by `ToolNode` begins in Stage 03.
- Approval UX for risky Python scripts lands in Stage 05.
- Project knowledge index, retriever, citations, and ContextItem packing land in Stage 06.
