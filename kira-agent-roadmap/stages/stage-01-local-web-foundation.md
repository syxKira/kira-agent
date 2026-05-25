# Stage 01: Local Web Foundation

## Goal

Create the first local Kira shell: a FastAPI backend, a Vite React frontend, an OpenAI-compatible provider adapter, a fixture provider, and a basic SSE event stream. A user first sees a focused welcome screen, clicks Start, enters a timeline-style agent workspace, starts a fixture-backed run, and sees visible assistant text stream without exposing hidden thinking as normal text.

## Why This Stage

Kira is not CLI/TUI-first. The first stage proves the local web development loop and provider/event contract before tools, graph workflows, or checkpointing add complexity.

## Scope

- FastAPI app with `/api/runs` and `/api/runs/{thread_id}/events`.
- Vite React app with a welcome screen and a run workbench.
- Timeline-style event UI inspired by chat/agent execution products: right-aligned user messages, left-aligned assistant reasoning/tool/status blocks, tool result cards, timestamps, and a bottom stop control.
- OpenAI-compatible provider interface.
- Fixture provider for deterministic local tests.
- Event normalization for visible text, hidden thinking, done, and error events.

Excluded:

- LangGraph workflow execution.
- Tool calls.
- Checkpointing or resume.
- Skills and memory.
- Production auth or remote deployment.

## Inputs And Dependencies

- Python backend.
- TypeScript frontend.
- FastAPI and Uvicorn for local backend.
- Vite React for local frontend.
- Provider config stored outside project secrets by default.

## Design

The backend exposes one run endpoint and one SSE endpoint. Stage 01 may keep run state in memory because durable checkpointing and graph reliability land in Stage 04. The provider adapter emits provider-neutral events:

```python
ProviderEvent = Literal["text_delta", "thinking_delta", "done", "error"]
```

The frontend has two routes or view states:

| View | Purpose |
| --- | --- |
| Welcome | Kira identity, local project/model status, Start button, recent run placeholders |
| Workbench | Timeline stream, prompt composer, running status, stop button, and compact side panels for skills/tools/state |

The workbench renders event groups in a vertical timeline:

- user prompt bubbles align to the right;
- assistant status rows show states such as `Thinking`, `Calling tool`, `Waiting for input`, and `Completed`;
- tool calls render as compact cards with a header, tool name pill, JSON/result preview, copy action, and collapsed/expanded detail;
- visible assistant text renders as normal answer blocks;
- hidden thinking may appear in debug metadata but not in the normal answer pane;
- a fixed bottom control bar shows composer when idle and Stop when a run is active.

## Implementation Tasks

1. Create Python backend project structure and local app entrypoint.
2. Create Vite React frontend structure.
3. Add local dev instructions for running backend and frontend.
4. Implement OpenAI-compatible provider interface.
5. Implement fixture provider with scripted event replay.
6. Implement SSE route for run events.
7. Add welcome screen with Start transition into the workbench.
8. Add timeline event stream view with user bubble, assistant status row, tool card, text block, timestamp, and stop button states.
9. Add tests for fixture replay, thinking filtering, and frontend event rendering.

## Validation

- Start backend locally and call `POST /api/runs`.
- Open frontend, click Start, and run a fixture script from the workbench.
- Verify visible text streams over SSE.
- Verify hidden thinking is not rendered as normal text.
- Verify fixture events render as timeline groups: user message, thinking/status row, tool card, assistant text, and done state.
- Backend tests pass without network or API keys.

## Exit Criteria

- Local web app has a welcome screen and can run a deterministic fixture-backed task in the workbench.
- Provider event types are documented and tested.
- Frontend and backend can be developed independently.

## Deferred Work

- Real graph execution begins in Stage 03.
- Durable session/checkpoint and graph reliability start in Stage 04.
- Full HITL UI starts in Stage 05.
