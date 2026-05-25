## 1. Shared Contracts

- [x] 1.1 Create Stage 01 shared run/event contracts under `src/` for run requests, run responses, run status, and normalized Kira events.
- [x] 1.2 Define event types for `text_delta`, `thinking_delta`, `done`, and `error` with `thread_id`, monotonic `seq`, and typed `data` payloads.
- [x] 1.3 Add contract examples or fixtures that backend and frontend tests can reuse without network access.

## 2. FastAPI Backend

- [x] 2.1 Create the `server/` FastAPI project structure and local app entrypoint.
- [x] 2.2 Implement in-memory Stage 01 run storage keyed by generated `thread_id`.
- [x] 2.3 Implement `POST /api/runs` to accept prompt text and optional fixture script, return `thread_id`, status, and event stream metadata.
- [x] 2.4 Implement `GET /api/runs/{thread_id}/events` as an SSE stream of ordered normalized events.
- [x] 2.5 Return a clear not-found API error when events are requested for an unknown `thread_id`.
- [x] 2.6 Keep checkpoint, resume, replay, run lock, idempotency, side-effect ledger, tool, retrieval, memory, and LangGraph endpoints out of Stage 01.

## 3. Provider And Fixture Streaming

- [x] 3.1 Add a provider interface that can wrap OpenAI-compatible streaming providers behind normalized Stage 01 events.
- [x] 3.2 Implement a fixture provider that replays scripted text, thinking, done, and error events deterministically.
- [x] 3.3 Normalize provider output into `text_delta`, `thinking_delta`, `done`, and `error` Kira events with stable sequencing.
- [x] 3.4 Include a welcome/demo fixture that streams visible assistant text and hidden thinking without requiring API keys.
- [x] 3.5 Include an error fixture for backend and frontend failure-state tests.

## 4. Vite React Frontend

- [x] 4.1 Create the `web/` Vite React project structure using the existing repository layout.
- [x] 4.2 Build `WelcomeScreen` with `Kira Agent`, local project/model or fixture readiness, disabled future-stage affordances where useful, and a primary Start action.
- [x] 4.3 Build `AgentWorkbench` with main timeline, compact inspector placeholder, and bottom control area.
- [x] 4.4 Build `PromptComposer` so idle users can submit a fixture-backed run from the workbench.
- [x] 4.5 Build SSE client logic that starts a run through `POST /api/runs` and streams events from `GET /api/runs/{thread_id}/events`.
- [x] 4.6 Render running state by disabling or replacing the composer with a Stop control state and progress summary.

## 5. Timeline Rendering

- [x] 5.1 Render user prompts as right-aligned timeline messages with timestamps.
- [x] 5.2 Render assistant thinking/status as left-aligned status rows without merging hidden thinking into answer text.
- [x] 5.3 Render visible `text_delta` content as normal assistant answer blocks.
- [x] 5.4 Render fixture tool-card preview events, if present in fixtures, as clearly labeled fixture timeline cards and not as real tool execution.
- [x] 5.5 Render `done` events as completed rows and return the workbench to idle composer state.
- [x] 5.6 Render `error` events as concise failure rows without treating errors as assistant text.
- [x] 5.7 Ensure desktop and narrow viewport layouts keep text wrapped and controls non-overlapping.

## 6. Documentation

- [x] 6.1 Update local development docs with backend startup command, frontend startup command, and the default fixture demo flow.
- [x] 6.2 Document Stage 01 boundaries: no Stage 02+ tools, LangGraph, checkpointing/resume, project knowledge retrieval, memory, production auth, or remote deployment.
- [x] 6.3 Document the Stage 01 event contract and hidden-thinking rendering rule.

## 7. Verification And Acceptance Checks

- [x] 7.1 Add backend tests proving `POST /api/runs` returns a unique `thread_id` and fixture runs require no network credentials.
- [x] 7.2 Add backend tests proving SSE streams ordered normalized events and unknown `thread_id` requests fail clearly.
- [x] 7.3 Add backend tests proving fixture replay is deterministic except for unique run identifiers and timestamps.
- [x] 7.4 Add frontend tests proving Welcome renders without backend events and Start enters the Workbench.
- [x] 7.5 Add frontend tests proving fixture runs render user message, status row, fixture card when present, visible assistant text, done state, and error state.
- [x] 7.6 Add frontend tests proving `thinking_delta` is not rendered in normal assistant answer blocks.
- [x] 7.7 Add responsive screenshot or DOM-layout checks for desktop and narrow widths with no overlapping critical text or controls.
- [x] 7.8 Run backend and frontend test suites locally and record the commands/results in the implementation summary.
