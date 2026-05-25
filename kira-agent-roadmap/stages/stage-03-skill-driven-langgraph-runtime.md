# Stage 03: Skill-driven LangGraph Runtime

## Goal

Introduce LangGraph as Kira's orchestration runtime without hardcoding a business workflow. Core compiles and runs skill-provided workflows through `StateGraph`, registers tools through `ToolNode`, and supports conditional edges.

## Why This Stage

The graph runtime should be generic before any workflow such as `planner -> gen_data -> send_kafka -> wait_ds -> reflect` appears. That sequence may become a skill workflow later, but core must not know it.

## Scope

- Skill discovery for workflow-capable skills.
- Workflow factory or declaration format for skills.
- `StateGraph` compile/run wrapper.
- `ToolNode` injection using Stage 02 tools.
- Conditional edge contract.
- Graph event mapping into KiraEvents.
- Run context carries selected provider/model metadata from the real LLM provider layer.
- Test skill workflow proving graph execution without hardcoded business nodes.
- Minimal node metadata needed by Stage 04 reliability: node type, allowed tools, timeout hint, side-effect hint, and retry hint.

Excluded:

- Built-in business workflows.
- Full skill package contract and progressive loading; Stage 06 deepens skills.
- SQLite checkpointing; Stage 04 adds durability.
- HITL interrupt UI; Stage 05 completes it.

## Inputs And Dependencies

- Stage 02 tool registry.
- Stage 01 run/event contract and the focused real LLM provider change: provider config, provider selection, fixture fallback, and stream mapping.
- LangGraph.
- Skill metadata convention.

## Design

Kira core exposes a graph runtime:

```python
class WorkflowSpec(TypedDict):
    name: str
    state_schema: str
    nodes: list[dict]
    edges: list[dict]
    tools: list[str]
```

A skill can provide either a Python workflow factory or a restricted declarative graph definition. In this stage the metadata is intentionally minimal; Stage 06 formalizes `SKILL.md`, `skill.yaml`, workflow fixtures, UI metadata, and permission declarations. Core validates the workflow, registers only allowed tools, compiles it into a `StateGraph`, and streams events. Node names and business semantics are owned by the skill.

`ToolNode` replaces a hand-written tool router. Conditional edges decide whether the graph continues, loops, branches, calls tools, or ends.

Stage 03 should stay intentionally thin: it proves that skill-defined graphs can run. It does not own retries or durable side-effect semantics yet, but it must preserve enough node metadata for Stage 04 to enforce them without changing every skill manifest later.

Provider selection remains outside workflow business logic. A run enters the graph with redacted provider metadata such as provider profile ID, selected model, whether fixture fallback was used, timeout, and retry budget. Graph nodes may call the selected model client through the core provider interface, but skills and graph declarations must not receive raw `apiKey` values or provider config objects.

Selection precedence entering Stage 03:

1. explicit run request provider/model override;
2. active skill model hint, if allowed by policy;
3. configured default provider/model;
4. fixture fallback when no valid API key is available.

## Implementation Tasks

1. Define skill workflow metadata.
2. Implement workflow-capable skill discovery.
3. Implement graph runtime wrapper around `StateGraph`.
4. Register Stage 02 tools into a `ToolNode`.
5. Add conditional edge helpers.
6. Map graph events into KiraEvents.
7. Thread redacted provider/model selection metadata through run context and graph state.
8. Add node metadata fields for timeout, retryability, model usage, and side-effect hints.
9. Add a test skill with generic nodes, one model call through the selected provider, and one tool call.
10. Add failure tests for missing tools, invalid edges, unsupported graph declarations, provider fallback, and request-level provider/model override.

## Validation

- Core loads and runs a test skill graph.
- Conditional edges can branch and terminate.
- ToolNode dispatches a registered tool without a custom router.
- No business node names are required by core.
- Node metadata can be read by Stage 04 reliability without hardcoding skill-specific logic.
- Model-using graph nodes consume provider output only through normalized KiraEvents.
- Raw API keys never enter graph state, skill manifests, checkpoints, or test fixtures.

## Exit Criteria

- Kira core is a workflow runtime, not a workflow implementation.
- A skill can supply a graph and tool set.
- Stage 04 can attach checkpointing and reliability policy to the compiled graph.

## Deferred Work

- Durable graph reliability, checkpointing, retry, and idempotency land in Stage 04.
- `interrupt` and frontend HITL land in Stage 05.
- Skill catalog, progressive loading, and context rules mature in Stage 06.
