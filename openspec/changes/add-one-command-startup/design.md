## Context

Kira is intentionally split into a Python FastAPI backend (`server/`) and a TypeScript Vite React frontend (`web/`). That split is useful for development and ownership, but the current startup model requires users to launch both services manually. It also causes an important deployment trap: the frontend defaults to `http://127.0.0.1:8000`, which is correct only when the browser and backend run on the same machine.

The target shape is a one-command experience with two modes:

- development mode starts FastAPI and Vite together while preserving hot reload;
- serve mode runs one FastAPI service that serves the built frontend and all existing `/api/*` endpoints from the same origin.

This change does not alter Kira's runtime semantics. Provider selection, graph execution, transcript continuity, project retrieval, memory, permissions, and hidden-thinking boundaries remain unchanged.

## Goals / Non-Goals

**Goals:**

- Provide one documented command for local development startup.
- Provide one documented command for complete single-service startup.
- Keep independent backend and frontend commands available for focused development.
- Make same-origin `/api` the frontend default, with an explicit API-base override only when needed.
- Preserve API/SSE routes under `/api/*` and serve the frontend shell for non-API browser routes.
- Keep provider secrets in user-local config or environment only, never in frontend bundles, logs, or docs.

**Non-Goals:**

- Add production authentication, user accounts, TLS, or public internet hardening.
- Replace Vite hot reload during frontend development.
- Merge backend and frontend source ownership into one package.
- Change runtime storage, provider config, graph execution, tools, skills, memory, or transcript semantics.
- Add a new external process manager dependency.

## Decisions

### Decision: Keep source split, unify runtime entrypoints

Kira will keep `server/` and `web/` as separate source areas. The one-command wrapper coordinates existing tools instead of moving frontend code into the Python package.

Alternative considered: merge the frontend into the server package as source. This would reduce visible directories but would blur ownership and make frontend hot reload worse. The roadmap explicitly preserves the `server/web/src` layout, so runtime unification is the smaller and cleaner change.

### Decision: Add a repo-local startup wrapper first

Add a repo-local command such as `scripts/kira dev` and `scripts/kira serve`.

- `dev` starts the backend and Vite dev server as child processes, prints the Vite URL, forwards environment options, and terminates both children on Ctrl-C or failure.
- `serve` ensures a frontend build exists or builds it, sets the frontend dist path for FastAPI, and starts one Uvicorn/FastAPI process.

Alternative considered: only add a Python console script. A package console script is useful later, but a repo-local wrapper is easier to run before installation and can orchestrate both `uv` and `pnpm` without changing package publishing.

### Decision: Frontend defaults to same-origin API URLs

The frontend API base will default to an empty string, so `fetch("/api/...")` and `EventSource("/api/...")` target the serving origin. `VITE_KIRA_API_BASE` remains available for explicit split-host deployments.

Alternative considered: keep `http://127.0.0.1:8000` as the default and document override. That keeps local split development working but breaks remote browsers by sending requests to the user's own loopback interface. Same-origin is safer for both single-service and proxied dev mode.

### Decision: Vite dev uses `/api` proxy

In development mode, Vite will proxy `/api` to the backend origin. The proxy target should be configurable by environment, with `http://127.0.0.1:8000` as the default.

Alternative considered: keep CORS-only split development. CORS still remains useful for advanced overrides, but proxying lets the same frontend code path exercise same-origin behavior during normal development.

### Decision: FastAPI serves static frontend only when configured or discoverable

FastAPI should mount frontend assets when a valid Vite `dist/index.html` path is configured or found. API routes must be registered before any frontend fallback. Non-API routes return the SPA `index.html`; missing static assets return bounded 404s rather than `index.html` so broken assets remain visible.

Alternative considered: always require frontend assets. That would make backend tests and API-only development brittle. Optional static serving preserves the current server-only loop.

### Decision: Single-service mode does not add security controls

The serve command can bind to `0.0.0.0` when requested, but documentation must state that this is not a production hardening feature. Remote exposure requires an external trusted network boundary or future authentication work.

Alternative considered: block non-localhost binds. That would prevent the user's target deployment shape. Warnings and explicit host flags keep the behavior intentional without pretending to solve auth.

## Risks / Trade-offs

- Static fallback intercepts API routes -> Register `/api` routes first and exclude `/api` from frontend fallback tests.
- Missing `pnpm`, Node, or frontend dependencies makes one-command serve fail -> Print clear remediation with the exact failing step and keep server-only commands documented.
- Dev wrapper leaves child processes behind -> Use process groups or explicit child termination and test signal/failure handling where practical.
- Same-origin default affects tests that assumed absolute API URLs -> Update API tests to assert relative defaults and explicit override behavior.
- Single-service mode is easier to expose remotely -> Document that this change adds packaging convenience, not authentication, TLS, or multi-user isolation.

## Migration Plan

1. Add the startup wrapper and document both one-command modes.
2. Change frontend API defaults to same-origin and add Vite proxy support.
3. Add optional FastAPI static frontend serving with route-order tests.
4. Add backend, frontend, and smoke tests for dev/serve startup behavior.
5. Keep existing separate startup commands documented as advanced/focused development paths.

Rollback is straightforward: users can continue running the existing independent backend and frontend commands. If static serving causes an issue, unset the frontend dist configuration and run API-only backend mode.

## Open Questions

- Should a later change promote the repo-local wrapper into a Python console script such as `uv run kira serve`?
- Should a later change add an official Dockerfile once the one-command local path is stable?
- What authentication or network-boundary model should be required before recommending remote public exposure?
