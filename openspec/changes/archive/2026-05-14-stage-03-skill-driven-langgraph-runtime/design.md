## Context

Kira currently has a FastAPI run API, SSE event normalization, deterministic fixture provider, real OpenAI-compatible provider selection, and a LangChain Core `StructuredTool` registry for Stage 02 tools. Runs are still provider-streaming or fixture-streaming directly; there is no graph runtime, skill workflow discovery, or tool dispatch through LangGraph.

Stage 03 introduces a narrow graph runtime that proves skill-defined workflows can run. The runtime must stay generic: node names, workflow shape, and business behavior belong to skills. Kira core owns validation, provider selection, tool allowlists, event mapping, and secret boundaries.

## Goals / Non-Goals

**Goals:**

- Add LangGraph as the workflow orchestration dependency for `server/`.
- Discover minimal workflow-capable skills and expose safe metadata through an API.
- Compile and run skill-defined workflows through `StateGraph`.
- Dispatch Stage 02 tools through `ToolNode` with per-workflow tool allowlists.
- Support conditional edges and terminal paths.
- Map graph, model, tool, done, and error activity into normalized Kira events.
- Thread redacted provider/model metadata through run context and graph state.
- Preserve Stage 01 fixture runs, Stage 02 tool APIs, and real provider fallback behavior.

**Non-Goals:**

- No checkpointing, durable resume, run locks, idempotency, side-effect ledger, or replay.
- No HITL interrupt UI or resume implementation.
- No full Stage 06 skill package contract, skill catalog UI, project knowledge injection, or progressive skill loading.
- No memory system, project knowledge retrieval index, citations, or context budgeting beyond minimal graph state fields.
- No business-specific workflow in Kira core.
- No LangChain agents, chains, memory, prompt templates, or provider abstractions.

## Decisions

### Decision: Add a dedicated `graph_runtime` backend package

Create `server/src/kira_server/graph_runtime/` with modules for state, workflow specs, validation, runtime execution, event mapping, and ToolNode integration.

Rationale: This keeps graph orchestration separate from provider adapters, API routes, and Stage 02 tool implementations.

Alternative considered: Add graph logic directly to `api/routes.py`. That would couple HTTP concerns to workflow compilation and make Stage 04 reliability harder to add.

### Decision: Use a minimal Stage 03 skill metadata convention

Add `server/src/kira_server/skills/` for workflow discovery. Stage 03 skills can be Python-defined test skills or restricted declarations loaded from a controlled local test skills directory. Public metadata includes `skill_id`, display name, description, workflow names, allowed tools, and node metadata. It excludes raw provider config, raw API keys, and arbitrary file content.

Rationale: Stage 03 needs skill-provided graphs, but Stage 06 owns the complete package contract. Keeping this convention small prevents premature skill packaging decisions.

Alternative considered: Implement the full `skill.yaml` package format now. That would pull Stage 06 into Stage 03 and increase migration risk.

### Decision: Support a typed internal `WorkflowSpec`

Represent workflow declarations with a typed structure containing:

- `name`
- `nodes`
- `edges`
- `tools`
- `entrypoint`
- `node_metadata`

Node metadata includes `node_type`, `allowed_tools`, `timeout_hint`, `retry_hint`, `side_effect_hint`, and `uses_model`. The runtime validates names, entrypoint, edge targets, duplicate IDs, unsupported node types, and tool allowlists before compiling.

Rationale: Stage 04 will need reliability hints, but Stage 03 should only record metadata and surface it for tests.

Alternative considered: Let arbitrary Python workflow factories compile their own graph with no intermediate validation. That would be flexible but would make tool policy and metadata guarantees hard to enforce.

### Decision: Route `skill_id` runs through graph execution, preserve default provider runs

`POST /api/runs` already accepts `skill_id`. Stage 03 should store the selected skill/workflow metadata in the run record when present. `GET /api/runs/{thread_id}/events` chooses graph runtime execution when the run has a workflow selection; otherwise it preserves the current provider/fixture stream path.

Rationale: This keeps existing local web behavior stable and lets Stage 03 be opt-in by selecting a skill.

Alternative considered: Convert every run into a graph run immediately. That increases blast radius and makes fixture/provider regression harder to isolate.

### Decision: Provider selection stays outside skills

Run creation continues to select provider/model through the existing provider layer. The graph receives redacted metadata and a callable model-provider boundary, not raw provider config or API keys. Skill model hints can be considered only through provider selection policy; they must not directly load config.

Rationale: Provider secrecy and fallback behavior are already implemented and tested. Graph state must not become a secret carrier.

Alternative considered: Let workflow nodes construct provider clients. That would duplicate config logic and risk key leakage.

### Decision: ToolNode receives only allowlisted Stage 02 tools

Expose a ToolNode adapter that builds a node from the Stage 02 `ToolRegistry` and the workflow's allowlist. Unknown or disallowed tools fail validation before graph compilation. Tool results are normalized into graph state and Kira events.

Rationale: Stage 02 policy remains the source of truth for tool behavior, while Stage 03 proves LangGraph dispatch works without a custom router.

Alternative considered: Continue using `ToolRegistry.invoke` directly from graph nodes. That would test tools but would not satisfy the Stage 03 ToolNode exit signal.

### Decision: Keep event types narrow unless tests require schema additions

The runtime maps provider output into existing `text_delta`, `thinking_delta`, `done`, and `error` events. Tool dispatch can use `text_delta` events with a structured `kind`, such as `graph_tool_result`, unless shared contracts are intentionally extended with graph-specific event types in `src/`.

Rationale: The current frontend already renders structured `text_delta` cards and hidden thinking safely. Avoiding unnecessary new event types keeps Stage 03 smaller.

Alternative considered: Add full final-architecture event types such as `tool_start`, `tool_result`, and `checkpoint` now. `checkpoint` belongs to Stage 04, and broad event expansion may force premature frontend work.

### Decision: Test with fixture fallback by default and opt-in real provider smoke

Default tests use fixture or mocked providers. A real provider smoke path can be added but must be skipped unless explicit environment/config opt-in is present.

Rationale: CI and local development must not require real API keys.

Alternative considered: Require real provider config for graph tests. That would make deterministic testing unreliable and violate the existing provider fallback contract.

## Risks / Trade-offs

- LangGraph event APIs may expose more detail than Kira wants → Keep a narrow event mapper and test exact public payloads.
- ToolNode construction may need direct access to registered `StructuredTool` instances → Add a controlled registry method for allowlisted tools instead of exposing mutable internals.
- Stage 03 skill metadata may drift toward Stage 06 package design → Name it explicitly as a minimal Stage 03 convention and cover only workflow runtime fields.
- Graph state may accidentally store raw provider config → Define a graph state model that stores redacted provider metadata and selected model only.
- Conditional edge support can become too general → Support a small set of declarative conditions and Python factory conditions for test skills, then defer richer policy to later stages.
- In-memory run state limits graph inspection → Accept this for Stage 03; durable state and replay are Stage 04.

## Migration Plan

1. Add `langgraph` to server dependencies.
2. Introduce graph runtime and skill discovery modules without changing default runs.
3. Add a test workflow-capable skill and `/api/skills` metadata endpoint.
4. Extend run records to store optional skill/workflow selection.
5. Route only `skill_id` runs through graph execution.
6. Preserve existing provider/fixture path for runs without `skill_id`.
7. Add tests, update shared docs/schemas if event metadata changes, and run OpenSpec validation.

Rollback is straightforward because graph execution is opt-in by `skill_id`; removing the graph route path restores the current provider/fixture behavior.

## Open Questions

- Should Stage 03 expose a minimal skill selector in the frontend, or keep frontend changes to TypeScript contracts and API reachability only?
- Should graph tool activity remain structured `text_delta` payloads for now, or should Stage 03 add explicit `tool_result` events ahead of the final architecture?
- Should Stage 03 support only built-in test skills, or also scan a user-local skills directory with strict validation?
