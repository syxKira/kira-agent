## 1. Dependencies And Module Layout

- [x] 1.1 Add the `langgraph` runtime dependency to `server/pyproject.toml` and refresh lock files as needed.
- [x] 1.2 Create `server/src/kira_server/graph_runtime/` with package modules for state, workflow specs, validation, runtime execution, ToolNode integration, and event mapping.
- [x] 1.3 Create `server/src/kira_server/skills/` with package modules for minimal Stage 03 skill metadata and discovery.
- [x] 1.4 Add tests that import the new packages and verify the app still starts without workflow-capable skills.

## 2. Skill Workflow Discovery

- [x] 2.1 Define minimal Stage 03 skill metadata models for skill ID, display name, description, workflow names, allowed tools, node metadata, and optional model hint.
- [x] 2.2 Implement a skill registry that can register built-in workflow-capable skills and ignore non-workflow skills.
- [x] 2.3 Add a generic built-in test skill with one model-using node, one tool-capable node, and conditional termination.
- [x] 2.4 Add `GET /api/skills` returning only safe public metadata.
- [x] 2.5 Add tests for discoverable test skill, empty registry behavior, unknown `skill_id`, and metadata redaction.

## 3. Workflow Spec And Validation

- [x] 3.1 Define internal `WorkflowSpec`, node, edge, conditional edge, and node metadata models.
- [x] 3.2 Validate entrypoint existence, duplicate node IDs, edge targets, unsupported node types, and unsupported declarations before compilation.
- [x] 3.3 Validate node metadata fields for node type, allowed tools, timeout hint, retry hint, side-effect hint, and model usage hint.
- [x] 3.4 Add tests for valid workflow specs, invalid edge targets, missing entrypoints, duplicate nodes, unsupported node types, and unsupported declaration shapes.

## 4. LangGraph Runtime Execution

- [x] 4.1 Implement a runtime wrapper that compiles valid workflow specs into LangGraph `StateGraph` instances.
- [x] 4.2 Initialize graph state from run context: prompt, thread ID, skill ID, project root, redacted provider metadata, selected model, and fixture fallback status.
- [x] 4.3 Implement model node execution through the existing provider interface without passing raw provider config into skill metadata or public graph state.
- [x] 4.4 Implement conditional edge helpers for branch, loop, and termination decisions.
- [x] 4.5 Add tests proving a generic test skill graph runs through `StateGraph` without hardcoded business node names.
- [x] 4.6 Add tests for conditional branch termination and conditional branch to the tool path.

## 5. ToolNode Dispatch

- [x] 5.1 Add a controlled way for `ToolRegistry` to expose allowlisted `BaseTool`/`StructuredTool` instances for graph dispatch.
- [x] 5.2 Implement ToolNode creation from workflow tool allowlists.
- [x] 5.3 Reject workflows that declare tools not registered in the Stage 02 registry.
- [x] 5.4 Ensure graph-invoked tools preserve Stage 02 validation, path safety, Python execution controls, and bounded output behavior.
- [x] 5.5 Add tests for allowed read-only file tool dispatch, allowed controlled Python dispatch, missing tool rejection, disallowed tool calls, and path escape rejection.

## 6. Run API Integration

- [x] 6.1 Extend run records to store optional selected skill/workflow metadata while preserving existing provider selection fields.
- [x] 6.2 Route `skill_id` runs through graph runtime execution in `/api/runs/{thread_id}/events`.
- [x] 6.3 Preserve current direct provider/fixture streaming behavior for runs without `skill_id`.
- [x] 6.4 Apply provider selection precedence for request override, validated skill model hint, config default, and fixture fallback.
- [x] 6.5 Add API tests for known skill run creation, unknown skill validation error, no-skill provider run, no-skill fixture run, provider override, model override, and fixture fallback.

## 7. Graph Event Mapping

- [x] 7.1 Implement graph event mapping into normalized Kira events with thread ID, sequence number, timestamp, type, and structured data.
- [x] 7.2 Map model visible output to `text_delta` and hidden reasoning/thinking content to `thinking_delta`.
- [x] 7.3 Map ToolNode success results to bounded structured event payloads that include tool name and status.
- [x] 7.4 Map graph validation failures, runtime exceptions, provider failures, and tool failures to structured `error` events or run creation errors.
- [x] 7.5 Ensure graph runs emit exactly one `done` event on normal completion and no Stage 04 checkpoint/resume/replay events.
- [x] 7.6 Add tests for event ordering, model output mapping, hidden thinking separation, tool result mapping, runtime error mapping, provider failure mapping, and single completion.

## 8. Contracts, Docs, And Frontend Compatibility

- [x] 8.1 Update shared schemas in `src/` if graph/tool event payloads require contract documentation.
- [x] 8.2 Update TypeScript types for skill metadata and any graph event payloads exposed to the frontend.
- [x] 8.3 Keep the frontend workbench rendering compatible with existing Stage 01/02 events and graph tool-result payloads.
- [x] 8.4 Update README/server docs with Stage 03 scope, `/api/skills`, and explicit non-goals.
- [x] 8.5 Add frontend tests only for touched contracts or rendering behavior.

## 9. Security And Boundary Tests

- [x] 9.1 Add tests proving raw API keys do not appear in skill metadata, graph state public snapshots, events, API responses, diagnostics, or test fixtures.
- [x] 9.2 Add tests proving no project write/edit/delete/patch/stage tool is available through workflow ToolNode dispatch.
- [x] 9.3 Add tests proving Stage 03 does not create SQLite checkpoints, durable replay records, run locks, side-effect ledgers, memory records, or retrieval indexes.
- [x] 9.4 Add regression tests proving Stage 01 fixture streams and Stage 02 tool metadata APIs still pass unchanged.

## 10. Validation

- [x] 10.1 Run backend tests for provider, tools, skills, and graph runtime.
- [x] 10.2 Run frontend tests/typecheck if TypeScript or rendering contracts are touched.
- [x] 10.3 Run `openspec validate "stage-03-skill-driven-langgraph-runtime" --strict`.
- [x] 10.4 Run `openspec status --change "stage-03-skill-driven-langgraph-runtime"` and confirm all artifacts are complete.
- [x] 10.5 Record verification commands and results in the implementation summary.
