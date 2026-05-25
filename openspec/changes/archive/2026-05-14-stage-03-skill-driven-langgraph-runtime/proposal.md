## Why

Kira now has the local web loop, Stage 02 tool registry, and real OpenAI-compatible provider layer needed to run real workflows. Stage 03 introduces LangGraph as the generic orchestration runtime so skills can provide workflows without hardcoding business node names or workflow logic into Kira core.

## What Changes

- Add a focused graph runtime layer around LangGraph `StateGraph`.
- Add workflow-capable skill discovery for a minimal Stage 03 skill metadata convention.
- Support a restricted workflow declaration or Python workflow factory for test skills.
- Validate workflow nodes, edges, allowed tools, and minimal reliability metadata before compilation.
- Register Stage 02 tools into a LangGraph `ToolNode` using per-workflow allowlists.
- Support conditional graph edges for branch, loop, and termination decisions.
- Thread selected provider/model metadata into graph run context without exposing raw provider config or API keys.
- Map graph execution, model output, tool results, completion, and failures into existing Kira event streams.
- Add a generic test skill graph that proves model calls and tool calls work through the runtime.

## Scope

- Backend-only runtime work in `server/`, with shared event/schema updates in `src/` if event contracts need to describe graph/tool events.
- Minimal API exposure for workflow-capable skills, such as `GET /api/skills`, and run request selection by `skill_id`.
- LangGraph dependency and thin integration using `StateGraph`, `ToolNode`, conditional edges, and streaming APIs.
- Stage 03 skill metadata only: enough to discover and run workflow-capable test skills.

## Non-goals

- No built-in business workflow such as planner/data-generation/Kafka/DS/reflect.
- No full Stage 06 skill package contract, progressive skill loading, skill catalog UI, or project knowledge injection.
- No SQLite checkpointing, durable resume, run locks, side-effect ledger, idempotency, or replay; those belong to Stage 04.
- No HITL interrupt UI or resume endpoint behavior beyond preserving existing Stage 02 placeholder semantics; Stage 05 owns HITL.
- No memory system, project knowledge retrieval index, or citation packing.
- No general shell tool and no project file write/edit/delete/patch/stage tools.

## Capabilities

### New Capabilities

- `skill-workflow-discovery`: Discover workflow-capable skills and expose safe skill/workflow metadata.
- `langgraph-runtime-execution`: Compile and run skill-defined workflows through a generic LangGraph runtime.
- `toolnode-tool-dispatch`: Dispatch Stage 02 tools through LangGraph `ToolNode` with workflow tool allowlists.
- `graph-event-streaming`: Map graph, model, tool, completion, and failure activity into Kira events with redacted provider context.

### Modified Capabilities

- None.

## Impact

- Adds a runtime dependency on `langgraph`.
- Adds new backend modules under `server/src/kira_server/graph_runtime/` and likely `server/src/kira_server/skills/`.
- Extends run creation and event streaming paths to route selected skill workflows when `skill_id` is present.
- Adds tests for skill discovery, workflow validation, graph execution, conditional edges, ToolNode dispatch, provider fallback, request provider/model override, and secret redaction.
- May extend frontend TypeScript contracts to understand skill metadata and additional Kira event kinds while preserving existing fixture/provider flows.

## Acceptance Criteria

- A generic test skill graph runs through `StateGraph` and emits normalized Kira events.
- The test skill graph can call one selected provider/model path and one Stage 02 tool through `ToolNode`.
- Conditional edges can branch and terminate without core knowing business node names.
- Missing tools, invalid edges, unsupported declarations, and provider failures produce structured errors.
- Raw API keys never enter skill manifests, graph state, emitted events, public API responses, test fixtures, or diagnostics.
- Default fixture/provider runs from Stage 01 and Stage 02 tool APIs continue to pass.

## Risks

- LangGraph event shapes may not map one-to-one with Kira events, so the mapper must stay narrow and tested.
- ToolNode integration can accidentally bypass Stage 02 tool policy if allowlists are not enforced before graph compilation.
- Skill workflow declarations can become a premature full skill package format; Stage 03 should keep only the metadata needed to prove runtime execution.
- Provider metadata can leak if graph state stores full selected provider config instead of redacted public metadata.
