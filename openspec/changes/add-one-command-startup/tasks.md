## 1. Frontend Same-Origin API

- [x] 1.1 Change the frontend API base default to same-origin paths while preserving `VITE_KIRA_API_BASE` as an explicit override.
- [x] 1.2 Normalize API-base joining so HTTP requests and `EventSource` URLs work with empty, relative, and absolute base values.
- [x] 1.3 Add or update frontend tests that assert default `/api` URLs and explicit override behavior.

## 2. Vite Development Proxy

- [x] 2.1 Add a Vite `/api` proxy to the backend origin with a configurable target and sensible local default.
- [x] 2.2 Update frontend local run documentation to describe same-origin proxy behavior and split-host override usage.
- [x] 2.3 Add a smoke or configuration-level check that the proxy target can be configured without source changes.

## 3. FastAPI Frontend Serving

- [x] 3.1 Add optional frontend-dist configuration for FastAPI using an environment variable and/or discoverable `web/dist` path.
- [x] 3.2 Serve Vite build assets and `index.html` from FastAPI when a valid frontend dist is configured.
- [x] 3.3 Add SPA fallback for non-API browser routes while preserving `/api/*` route precedence and API 404 behavior.
- [x] 3.4 Add backend tests for `GET /`, existing `/api/health`, unknown `/api/*`, browser fallback routes, and missing static assets.

## 4. One-Command Startup Wrapper

- [x] 4.1 Add a repo-local startup command with `dev` and `serve` subcommands.
- [x] 4.2 Implement `dev` mode to start backend and Vite child processes, print the frontend URL, and terminate both children on interrupt or failure.
- [x] 4.3 Implement `serve` mode to build or verify frontend output, start one FastAPI/Uvicorn process, and print the FastAPI URL.
- [x] 4.4 Add host, port, frontend port, API port, build/no-build, and backend-origin configuration flags where needed.
- [x] 4.5 Ensure startup output redacts provider secrets and reports missing prerequisites or port failures clearly.

## 5. Smoke Coverage

- [x] 5.1 Add a local smoke path for one-command dev startup reachability and clean shutdown.
- [x] 5.2 Add a local smoke path for single-service startup that verifies `GET /`, `GET /api/health`, fixture run creation, and event streaming.
- [x] 5.3 Keep smoke tests fixture-first so they pass without real provider credentials or network access by default.

## 6. Documentation And Validation

- [x] 6.1 Update `server/README.md`, `web/README.md`, or root documentation with one-command dev and serve instructions.
- [x] 6.2 Document prerequisites, provider config expectations, same-origin behavior, remote bind warnings, and troubleshooting steps.
- [x] 6.3 Run backend tests, frontend typecheck/tests/build, and the new one-command smoke checks.
- [x] 6.4 Run `openspec validate add-one-command-startup --strict` and fix any validation errors.
