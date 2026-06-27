## ADDED Requirements

### Requirement: One command starts the local development loop
Kira SHALL provide a documented one-command development startup path that starts the FastAPI backend and Vite frontend together while preserving the normal development hot-reload workflow.

#### Scenario: Development startup prints a usable URL
- **WHEN** a user runs the documented development startup command from the repository root
- **THEN** the command starts the backend service and the Vite frontend service
- **THEN** the command prints the frontend URL that the user can open
- **THEN** the workbench can call `/api/health` through the development proxy

#### Scenario: Development startup terminates child processes
- **WHEN** the user interrupts the development startup command
- **THEN** the command terminates both backend and frontend child processes
- **THEN** it exits without leaving the managed Kira servers running

#### Scenario: Development startup reports missing prerequisites
- **WHEN** `uv`, `pnpm`, frontend dependencies, or required local ports are unavailable
- **THEN** the command exits with a non-zero status
- **THEN** the output identifies the missing prerequisite or failing startup step

### Requirement: One command starts complete single-service mode
Kira SHALL provide a documented one-command serve path that starts one FastAPI service capable of serving the built frontend and existing backend APIs from the same origin.

#### Scenario: Serve startup exposes the full app from FastAPI
- **WHEN** a user runs the documented serve startup command
- **THEN** one Uvicorn/FastAPI service starts
- **THEN** `GET /` returns the Kira frontend shell
- **THEN** `GET /api/health` returns the backend health response
- **THEN** the frontend can create runs and stream events using same-origin `/api` URLs

#### Scenario: Serve startup handles missing frontend build output
- **WHEN** the serve command starts and the configured frontend build output is missing
- **THEN** it either builds the frontend before starting FastAPI or exits with a clear remediation message
- **THEN** it does not start a misleading partial service that serves a blank frontend

#### Scenario: Serve startup supports explicit host and port
- **WHEN** the user passes documented host or port options to the serve command
- **THEN** the FastAPI service binds using those values
- **THEN** the printed URL reflects the configured host and port

### Requirement: Frontend API calls default to same origin
The frontend SHALL use same-origin `/api` URLs by default for HTTP requests and SSE connections, while retaining an explicit environment override for split-host deployments.

#### Scenario: Default API base is same origin
- **WHEN** the frontend is built or served without `VITE_KIRA_API_BASE`
- **THEN** API requests use paths such as `/api/runs`
- **THEN** event streams use relative `/api/runs/{thread_id}/events` URLs
- **THEN** the frontend does not default to `http://127.0.0.1:8000`

#### Scenario: Explicit API base override is honored
- **WHEN** `VITE_KIRA_API_BASE` is set to an absolute backend origin
- **THEN** frontend HTTP requests use that origin for `/api` paths
- **THEN** event streams use that origin for relative event URLs returned by the backend

### Requirement: Vite development proxies API traffic
The Vite development server SHALL proxy same-origin `/api` browser requests to the configured backend origin during development.

#### Scenario: Development proxy forwards API calls
- **WHEN** the frontend is served by Vite in development mode
- **THEN** browser requests to `/api/health` are forwarded to the backend service
- **THEN** the frontend code path remains compatible with single-service same-origin mode

#### Scenario: Development proxy target is configurable
- **WHEN** the backend development service uses a non-default host or port
- **THEN** the Vite proxy target can be configured without changing frontend source code

### Requirement: FastAPI serves the built SPA without intercepting APIs
The FastAPI app SHALL serve Vite build assets and SPA fallback routes only after preserving existing `/api/*` route behavior.

#### Scenario: API routes take precedence over frontend fallback
- **WHEN** a request targets an existing `/api/*` route
- **THEN** FastAPI returns the existing API response
- **THEN** the response is not replaced by the frontend `index.html`

#### Scenario: Unknown API route remains an API error
- **WHEN** a request targets an unknown `/api/*` route
- **THEN** FastAPI returns a backend not-found response
- **THEN** the response is not replaced by the frontend `index.html`

#### Scenario: Browser routes return SPA shell
- **WHEN** a request targets a non-API browser route such as `/conversation/example`
- **THEN** FastAPI returns the built frontend `index.html`
- **THEN** the frontend router can render or recover from the route

#### Scenario: Missing static asset remains visible
- **WHEN** a request targets a missing built asset path
- **THEN** FastAPI returns a bounded not-found response
- **THEN** it does not silently return the SPA shell for that missing asset

### Requirement: One-command startup preserves Kira safety boundaries
The one-command startup paths SHALL preserve Kira's existing provider secrecy, fixture fallback, transcript, event, and tool safety boundaries.

#### Scenario: Provider secrets are not printed or bundled
- **WHEN** one-command startup uses a real provider configuration
- **THEN** startup logs and frontend assets do not include raw API keys, authorization headers, cookies, private keys, or provider config secrets

#### Scenario: Missing provider config still allows fixture fallback
- **WHEN** no valid provider config is available
- **THEN** the one-command startup path still allows the local workbench to run fixture-backed flows according to existing provider fallback behavior
