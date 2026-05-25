## Why

Kira needs a local web foundation before graph orchestration, tools, retrieval, memory, or reliability work can be added safely. This change establishes the Stage 01 FastAPI + Vite React development loop and proves the provider-neutral run event contract with deterministic fixture streaming.

## What Changes

- Add a FastAPI backend under `server/` with local run creation and SSE event streaming endpoints.
- Add a Vite React frontend under `web/` with a welcome screen that enters a timeline-style run workbench.
- Add shared Stage 01 run and event schemas/contracts under `src/` for backend/frontend alignment.
- Add an OpenAI-compatible provider abstraction plus a deterministic fixture provider for local development and tests.
- Normalize provider events for visible assistant text, hidden thinking, completion, and errors.
- Render fixture-backed run events as timeline groups without showing hidden thinking as normal assistant text.
- Document local backend/frontend startup and Stage 01 acceptance checks.
- Defer Stage 02+ capabilities including tools, LangGraph workflows, checkpointing/resume, project knowledge retrieval, memory, and safety polish.

## Capabilities

### New Capabilities

- `local-run-api`: FastAPI local run creation, in-memory Stage 01 run state, and SSE event streaming.
- `provider-fixture-streaming`: Provider-neutral event contracts, OpenAI-compatible provider adapter boundary, and deterministic fixture replay.
- `local-web-workbench`: Vite React welcome screen, prompt composer, running/stop states, and timeline rendering for Stage 01 events.

### Modified Capabilities

- None.

## Impact

- Affected layout: `server/` for the FastAPI backend, `web/` for the Vite React frontend, and `src/` for shared schemas/contracts.
- New local API surface: `POST /api/runs` and `GET /api/runs/{thread_id}/events`.
- New development dependencies may include FastAPI/Uvicorn backend packages and Vite/React frontend packages.
- Tests must run without network access or API keys by using fixture replay.
- Stage 01 intentionally does not add LangGraph, LangChain tools, checkpointing, resume, retrieval, memory, production auth, or remote deployment.
