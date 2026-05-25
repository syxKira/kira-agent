## 1. Dependency And Contracts

- [x] 1.1 Add `langchain-core` to the server dependency set without adding LangChain agents, chains, memory, or provider integrations.
- [x] 1.2 Define shared `ToolResult` and tool metadata shapes for `ok`, `code`, `message`, `data`, `metadata`, and `truncated`.
- [x] 1.3 Add shared schema or fixture examples for `GET /api/tools` and representative success/error `ToolResult` payloads.
- [x] 1.4 Document Stage 02 boundaries in backend or root docs: no graph dispatch, no retrieval index, no file mutation, no general shell, and no HITL resume UI.

## 2. Tool Registry And API

- [x] 2.1 Create backend tooling modules for registry, tool metadata export, result normalization, and execution wrappers.
- [x] 2.2 Register `list_project_files`, `search_project_files`, `read_project_file`, `run_python_script`, and `ask_user_question` as LangChain Core compatible tools.
- [x] 2.3 Implement result normalization for success, validation error, permission error, not-found error, binary/large-file error, timeout error, and execution error.
- [x] 2.4 Add `GET /api/tools` returning tool name, description, argument JSON Schema, result schema metadata, and read/write risk classification.
- [x] 2.5 Ensure Stage 02 registry exposes no file write/edit/delete/stage tools, general shell tools, graph dispatch, memory tools, or checkpoint/resume tools.

## 3. Project Root And File Policy

- [x] 3.1 Implement a project root resolver that canonicalizes roots and returns stable root metadata.
- [x] 3.2 Reject path traversal and symlink escape before listing, searching, reading, or executing files.
- [x] 3.3 Implement built-in ignore defaults for `.git`, dependency directories, build outputs, caches, and sensitive hidden directories.
- [x] 3.4 Respect `.gitignore` where practical and expose ignore or omitted metadata where useful.
- [x] 3.5 Implement binary detection, large-file checks, output caps, relative path normalization, mtime, size, and cheap content hash metadata.

## 4. Read-only Project File Tools

- [x] 4.1 Implement `list_project_files(root?, glob?, limit?)` with `rg --files` preferred and Python fallback available.
- [x] 4.2 Ensure file listing returns bounded relative paths, root metadata, result count, omitted count, and truncation status.
- [x] 4.3 Implement `search_project_files(query, root?, glob?, limit?)` with `rg` preferred and Python fallback available.
- [x] 4.4 Ensure search returns bounded matches with relative path, line number, preview text, file metadata, omitted count, and truncation status.
- [x] 4.5 Implement `read_project_file(path, offset?, limit?)` for bounded text file slices.
- [x] 4.6 Ensure read results include path, root ID, file size, mtime, line or byte range, content hash when cheap, and truncation status.
- [x] 4.7 Ensure file tools never write, move, delete, patch, format, stage, or mutate project files.

## 5. Controlled Python Execution

- [x] 5.1 Implement `run_python_script` using argv-only Python subprocess execution with no shell invocation.
- [x] 5.2 Validate script path and cwd against allowed project roots before starting a subprocess.
- [x] 5.3 Filter subprocess environment variables through a minimal allowlist.
- [x] 5.4 Enforce timeout and terminate timed-out subprocesses with structured timeout results.
- [x] 5.5 Apply independent stdout and stderr caps with truncation metadata.
- [x] 5.6 Return exit code, stdout, stderr, duration, cwd, and truncation metadata in the `ToolResult` envelope.

## 6. HITL Question Placeholder

- [x] 6.1 Implement `ask_user_question` as a structured tool returning pending question payloads and stable question IDs.
- [x] 6.2 Validate non-empty question text and optional response field definitions.
- [x] 6.3 Ensure the placeholder does not add interrupt/resume endpoints, approval UI, or blocking frontend behavior.

## 7. Verification And Acceptance Checks

- [x] 7.1 Add tests proving `GET /api/tools` returns schemas for all five built-in tools.
- [x] 7.2 Add tests proving tool argument validation errors are normalized into `ToolResult` instead of uncaught tracebacks.
- [x] 7.3 Add tests proving path traversal and symlink escape are rejected.
- [x] 7.4 Add tests proving ignored directories, binary files, large files, and oversized reads return bounded structured results.
- [x] 7.5 Add tests proving file listing and search work with `rg` unavailable through the Python fallback.
- [x] 7.6 Add tests proving read-only file tools do not expose mutation operations.
- [x] 7.7 Add tests proving `run_python_script` enforces cwd boundary, env allowlist, timeout, no-shell execution, and output caps.
- [x] 7.8 Add tests proving `ask_user_question` returns a pending question payload and rejects invalid question text.
- [x] 7.9 Run backend tests and OpenSpec validation, then record commands and results in the implementation summary.
