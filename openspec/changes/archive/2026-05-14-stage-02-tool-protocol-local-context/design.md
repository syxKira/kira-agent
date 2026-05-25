## Context

Stage 01 established the local FastAPI/Vite shell, fixture provider, and SSE event stream. Stage 02 adds the first real tool layer so later graph work can depend on stable tool schemas and result envelopes instead of ad hoc backend functions.

The tool layer must be useful before LangGraph exists, but it must also remain compatible with future LangGraph `ToolNode` dispatch. The implementation should use only `langchain-core` tool primitives and avoid LangChain agents, chains, memory, prompt templates, or provider abstractions. Local file access is read-only project context, not a retrieval system. Controlled Python execution is a Python subprocess tool, not a shell.

## Goals / Non-Goals

**Goals:**

- Register built-in tools through a single backend registry using LangChain Core `BaseTool` or `@tool` compatible definitions.
- Expose `GET /api/tools` with tool names, descriptions, argument schemas, and result schema metadata.
- Normalize tool invocation outcomes into a stable `ToolResult` envelope.
- Implement read-only project file tools for listing, searching, and bounded text reads.
- Enforce project root, traversal, symlink, ignore, binary, large-file, and output cap policies before returning local file content.
- Implement controlled `run_python_script` with bounded cwd, environment allowlist, timeout, stdout/stderr caps, and no shell expansion.
- Implement `ask_user_question` as a structured placeholder result that later stages can map to HITL interrupt/resume.
- Add tests for schema export, validation, root safety, fallback behavior, binary/large files, timeouts, and output caps.

**Non-Goals:**

- No LangGraph `ToolNode` dispatch or graph runtime.
- No LangChain agents, chains, memory, prompt templates, or model orchestration.
- No file write, move, delete, patch, format, staging, git, or general shell tools.
- No project knowledge index, chunking, ranking, citations, stale markers, or ContextItem packing.
- No frontend HITL approval panel or resume endpoint.
- No durable audit database, checkpointing, resume, retries, run locks, or side-effect ledger.

## Decisions

### Use LangChain Core only at the tool boundary

Built-in tools will be declared as `BaseTool` or `@tool` compatible callables with typed inputs and docstrings so JSON Schema can be derived from the same definitions future `ToolNode` dispatch will use. Kira wraps execution and export rather than exposing LangChain internals directly.

Alternative considered: use plain FastAPI/Pydantic functions and convert later. That would be faster initially, but it risks schema drift when Stage 03 introduces `ToolNode`.

### Normalize all tool outcomes through `ToolResult`

Every tool call should return a consistent envelope:

```python
class ToolResult(TypedDict, total=False):
    ok: bool
    code: str
    message: str
    data: dict
    metadata: dict
    truncated: bool
```

Validation errors, permission errors, not-found errors, binary/large-file rejects, subprocess timeouts, and internal errors all use the same envelope shape. Tool-specific payloads live under `data`, while root/path/range/hash/truncation facts live under `metadata`.

Alternative considered: raise exceptions to callers. That makes API testing harder and forces Stage 03 graph dispatch to special-case failures.

### Keep project file tools primitive and read-only

Stage 02 implements `list_project_files`, `search_project_files`, and `read_project_file` as safe primitives. These tools return stable metadata that Stage 06 can reuse, but they do not build inventory tables, chunks, citations, retrieval rankings, or prompt ContextItems.

Alternative considered: implement Stage 06 retrieval APIs now. That would blur the stage boundary and force indexing/citation decisions before the basic file policy is tested.

### Resolve roots before all local file operations

All local file tools and Python execution use a project root resolver. The resolver canonicalizes the requested root, rejects traversal and symlink escape, applies built-in ignores, and keeps all returned paths relative to the resolved root in API payloads.

Alternative considered: trust frontend-supplied paths. That is too risky because later model-driven tool calls will use the same contracts.

### Prefer `rg`, keep Python fallbacks testable

`list_project_files` and `search_project_files` prefer `rg` when available, because it respects common ignore behavior and is fast. A Python fallback must remain available and covered by tests so local development does not depend on `rg` being installed.

Alternative considered: implement only Python traversal. That simplifies dependencies but gives worse behavior on larger projects and ignores a common, faster local tool.

### Execute Python without shell semantics

`run_python_script` invokes the Python executable with an argv list, never through a shell. It accepts a project-relative script path or system-created temporary script reference, validates cwd under the allowed root, filters environment variables through an allowlist, enforces timeout, and truncates stdout/stderr independently.

Alternative considered: expose a general shell command runner. That is explicitly out of scope and would conflict with the roadmap's safety boundary.

## Risks / Trade-offs

- `rg` and Python fallback results can differ in exact ordering or ignore semantics -> Tests should assert shared safety and caps, not identical implementation ordering.
- `.gitignore` compatibility can become complex -> Implement practical support and document remaining edge cases instead of recreating git's full matcher.
- Metadata hashing can add overhead on large files -> Compute hashes only for bounded readable results or when cheap, and report omitted hash metadata when skipped.
- Python execution could become a shell by accident -> Use argv-only subprocess calls, cwd validation, env allowlist, timeout, and tests that reject shell-like inputs.
- Tool result schemas can drift from implementation -> Derive input schemas from tool definitions and add schema snapshot/shape tests for `GET /api/tools`.
- `ask_user_question` is not interactive in Stage 02 -> Return a structured pending-question result only, and defer interrupt/resume UI to Stage 05.

## Migration Plan

1. Add `langchain-core` to server dependencies.
2. Add backend tool modules for registry, result normalization, project root policy, local file tools, Python execution, and HITL placeholder.
3. Add `GET /api/tools` without changing Stage 01 run/SSE endpoints.
4. Add shared schemas/examples for `ToolResult` and tool metadata if needed by frontend tests or future implementation.
5. Add backend tests and update docs for Stage 02 boundaries.

Rollback is removing the Stage 02 tool modules, dependency, route, schemas/examples, tests, and docs while leaving Stage 01 run/SSE behavior unchanged.

## Open Questions

- The default allowed project root should likely be the repository root in local development, with an explicit override in tests.
- The env allowlist for `run_python_script` should start minimal, such as `PYTHONPATH`, `PATH`, and explicitly configured Kira test variables.
- The implementation should decide whether temporary script references are required in Stage 02 or whether project-relative script paths are sufficient for the first pass.
