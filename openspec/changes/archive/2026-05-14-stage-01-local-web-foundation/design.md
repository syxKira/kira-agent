## Context

Stage 01 creates the first usable local Kira shell. The repository already defines the intended layout: `server/` for the Python FastAPI backend, `web/` for the Vite React frontend, and `src/` for shared schemas/contracts. The roadmap requires this stage to prove the local web loop, fixture-backed runs, provider-neutral event normalization, and a timeline-style workbench before adding Stage 02+ tools or graph runtime complexity.

The implementation must stay intentionally narrow. Run state can be in memory, because durable checkpointing and resume arrive in Stage 04. Tool events can be represented by fixtures for UI readiness, but no real tools, LangChain tools, LangGraph workflows, project retrieval, memory, or safety polish are part of this change.

## Goals / Non-Goals

**Goals:**

- Provide a local FastAPI app with `POST /api/runs` and `GET /api/runs/{thread_id}/events`.
- Provide a local Vite React app whose first screen is a welcome screen and whose primary working view is a timeline-style run workbench.
- Define shared Stage 01 contracts for run requests, run metadata, and normalized Kira events.
- Implement a provider abstraction that can support an OpenAI-compatible provider later while using a fixture provider for deterministic Stage 01 development and tests.
- Stream visible assistant text, hidden thinking, completion, and error events over SSE.
- Render hidden thinking as status/debug metadata only, never as normal assistant answer text.
- Add backend and frontend tests that run without network access or API keys.

**Non-Goals:**

- No Stage 02 tools, LangChain `BaseTool` registry, controlled Python execution, or project file tools.
- No Stage 03 LangGraph workflow execution or skill workflow loader.
- No Stage 04 checkpointing, resume, run locks, replay, idempotency, retries, or side-effect ledger.
- No Stage 05 HITL resume behavior beyond non-functional fixture timeline placeholders if needed for layout.
- No Stage 06+ project knowledge retrieval, memory, audit system, packaging, or safety hardening.
- No production auth, hosted deployment, or persistent database.

## Decisions

### Use in-memory run state for Stage 01

The backend will create a `thread_id` for each run and store the selected fixture script, prompt, status, and event cursor in process memory. This keeps Stage 01 focused on API shape and streaming behavior. The alternative, adding SQLite-backed sessions now, would overlap with Stage 04 reliability and create premature migration surface.

### Treat SSE as the frontend/backend event contract

`GET /api/runs/{thread_id}/events` will stream newline-delimited SSE messages with monotonic `seq` values and a normalized `KiraEvent` payload. The frontend consumes this contract directly and renders the timeline from received events. The alternative, polling run state, would not prove the streaming UI required by the roadmap.

### Define provider-neutral events before provider-specific adapters

Provider implementations emit internal provider events, then the backend normalizes them into Stage 01 `KiraEvent` values: `text_delta`, `thinking_delta`, `done`, and `error`. Fixture-only UI preview events such as tool-card examples must remain clearly fixture data and must not imply real tool execution. The alternative, passing raw provider chunks to the browser, would couple the UI to provider-specific details too early.

### Keep shared contracts small and Stage 01-specific

Shared contracts under `src/` will cover request/response/event shapes that both backend and frontend need. They must not introduce full final-architecture types such as ContextItem budgeting, memory citations, graph state, tool schemas, or checkpoint records. The alternative, copying the final Stage 08 data model into Stage 01, would blur stage boundaries.

### Build the actual workbench as the first product surface

The frontend will open on a focused welcome screen with local project/model readiness and a Start action. Start transitions to the workbench without requiring a model call. The workbench contains the prompt composer, run timeline, inspector placeholder, and running Stop state. The alternative, a marketing-style landing page or dashboard-first UI, does not satisfy the frontend experience direction.

## Risks / Trade-offs

- In-memory run state is lost on backend restart -> Accept for Stage 01 and document that persistence starts in Stage 04.
- SSE reconnection semantics are limited -> Include monotonic `seq` fields now, but defer durable replay and resume to Stage 04.
- Fixture tool cards could be mistaken for real tool support -> Label them as fixture timeline events and do not expose real tool endpoints or tool execution.
- Hidden thinking could leak into assistant answer text -> Add explicit backend normalization and frontend rendering tests that verify `thinking_delta` is excluded from normal answer blocks.
- Backend and frontend contract drift could occur -> Keep shared schemas/contracts in `src/` and add contract-oriented tests around fixture events.

## Migration Plan

This is a new local foundation with no existing runtime migration. Implementation can be introduced by adding the `server/`, `web/`, and `src/` Stage 01 files and documenting local startup commands. Rollback is removing the new Stage 01 files and OpenSpec change artifacts before implementation is archived.

## Open Questions

- Exact package manager lockfile updates should follow the existing repository convention once implementation inspects `web/` and root package metadata.
- The first fixture script name can be chosen during implementation, but it must include visible text, hidden thinking, done, and error-test coverage.
