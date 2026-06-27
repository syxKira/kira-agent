## Why

Kira currently requires users to understand and start the FastAPI backend and Vite frontend as separate services. This creates avoidable deployment friction and makes a remote or shared server setup easy to misconfigure, especially because frontend requests can accidentally target the browser user's own `127.0.0.1`.

This change gives Kira a first-class one-command startup path for both local development and complete single-service operation while preserving the existing backend/frontend ownership boundaries.

## What Changes

- Add a one-command development startup path that starts the backend and Vite frontend together, coordinates shutdown, and prints the usable local URL.
- Add a one-command serve startup path that builds or verifies the frontend bundle, starts one FastAPI service, and serves both `/` frontend routes and `/api/*` backend routes from the same origin.
- Update the frontend API client to use same-origin API URLs by default, while keeping an explicit environment override for advanced deployments.
- Add Vite development proxy support so the same frontend API code works in both dev and single-service modes.
- Add FastAPI static frontend hosting for the Vite `dist` output with SPA fallback for non-API routes.
- Document the one-command paths, configuration knobs, provider secret expectations, and troubleshooting behavior.
- Add smoke coverage for the one-command flows and same-origin API behavior.

## Capabilities

### New Capabilities

- `one-command-startup`: Defines Kira's supported one-command startup modes, including combined dev startup, single-service frontend/backend serving, same-origin API behavior, and shutdown/error expectations.

### Modified Capabilities

- `local-packaging-smoke`: Expands local packaging documentation and smoke requirements to cover the new one-command dev and serve paths.

## Scope

- Keep `server/`, `web/`, and `src/` as separate ownership areas.
- Support local developer usage through one command without removing the independent backend and frontend commands.
- Support a complete single-process runtime where FastAPI serves the built frontend and existing API/SSE routes.
- Keep provider secrets outside the repository and preserve fixture fallback when no real provider is configured.
- Keep frontend hidden-thinking and transcript behavior unchanged.

## Non-goals

- No production authentication, user management, or public internet hardening.
- No container image implementation unless needed as a small optional documentation hook.
- No change to provider selection, graph runtime, tools, memory, transcript semantics, or skill workflow behavior.
- No replacement of Vite development hot reload for normal frontend development.
- No removal of the existing separate `uvicorn` and `pnpm dev` commands.

## Acceptance Criteria

- A user can run one documented command for development and get a working Kira URL without manually launching backend and frontend terminals.
- A user can run one documented command for single-service operation and access the complete app from the FastAPI origin.
- Frontend API calls and SSE connections work when served from the same origin and do not default to the browser user's `127.0.0.1`.
- API routes remain under `/api/*`, and non-API frontend routes return the built SPA shell.
- Missing frontend build output produces a clear remediation path instead of a blank or misleading app.
- Existing backend tests and frontend tests remain runnable independently.

## Risks

- Static SPA fallback could accidentally intercept API errors if route ordering is wrong.
- A one-command dev wrapper must terminate child processes reliably to avoid orphaned servers.
- Building frontend assets from a Python-facing command can introduce Node/pnpm availability failures that need clear messages.
- Single-service deployment can make Kira easier to expose remotely, so docs must warn that this does not add authentication or public hardening.

## Impact

- Backend: FastAPI app startup/static mounting, optional frontend-dist configuration, tests for static serving and route ordering.
- Frontend: API base default, EventSource URL handling, Vite proxy configuration, tests for same-origin URL construction.
- Scripts/CLI: one-command startup wrapper for dev and serve modes.
- Docs/OpenSpec: local startup, packaging smoke, and troubleshooting documentation.
