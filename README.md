# Kira Agent

Kira Agent is a local web agent for general task execution and project-aware assistance. It is not a code-specialized agent: the core runtime focuses on chat, provider streaming, skills, read-only project knowledge retrieval, local memory, traceability, and controlled tool execution.

Business workflows should live in skills under `.kira/skills`, while the core app stays provider-neutral and workflow-neutral.

## Project Layout

```text
kira-agent/
  server/   FastAPI backend
  web/      Vite React frontend
  src/      Shared API schemas and contracts
  .kira/    Project-local skills
```

## Start Locally

Prerequisites: `uv`, `pnpm`, Node.js, and Python 3.10+.

Recommended one-command development startup:

```bash
scripts/kira dev
```

Open the printed Vite URL, usually:

```text
http://127.0.0.1:5173/
```

For a complete single-service run, build or verify the frontend bundle and serve both the web app and API from FastAPI:

```bash
scripts/kira serve --build
```

Open the printed FastAPI URL, usually:

```text
http://127.0.0.1:8000/
```

`serve` mode uses same-origin `/api` requests and `KIRA_WEB_DIST` internally. Binding to `0.0.0.0` is supported with `--host 0.0.0.0`, but this does not add authentication, TLS, or public internet hardening.

Focused backend/frontend development can still use separate terminals:

```bash
cd server
uv run uvicorn kira_server.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd web
pnpm install
pnpm dev
```

The frontend now uses same-origin `/api` by default. In Vite development, `/api` is proxied to `http://127.0.0.1:8000`; override the proxy target when needed:

```bash
cd web
VITE_KIRA_DEV_API_TARGET=http://127.0.0.1:9000 pnpm dev
```

Use `VITE_KIRA_API_BASE` only for explicit split-host frontend deployments where browser requests should target a different API origin.

## Troubleshooting Startup

- Missing `uv` or `pnpm`: install the missing command and rerun `scripts/kira dev` or `scripts/kira serve --build`.
- Port already in use: pass `--api-port` or `--web-port` to `scripts/kira dev`, or `--port` to `scripts/kira serve`.
- Missing frontend build: run `scripts/kira serve --build`, or run `cd web && pnpm build` before `scripts/kira serve --no-build`.
- Backend on a custom port during Vite development: set `VITE_KIRA_DEV_API_TARGET=http://127.0.0.1:<port>`.
- Missing provider config: local fixture fallback still works; real provider config belongs in `~/.kira-agent/config.yaml` or `KIRA_CONFIG_PATH`, not in this repo.

## Provider Config

Real provider secrets are loaded from `~/.kira-agent/config.yaml` by default, or from `KIRA_CONFIG_PATH` when set. Keep real keys outside this repo.

Example:

```yaml
default_provider: minimax-global
providers:
  minimax-global:
    preset: Minimax Global
    provider: openai
    baseURL: https://api.minimax.io/v1
    model: MiniMax-Text-01
    api_key: replace-with-your-key
```

When no valid provider key is configured, Kira can fall back to deterministic fixture behavior for local development.

## Useful Checks

Backend tests:

```bash
cd server
uv run --extra dev pytest
```

Frontend checks:

```bash
cd web
pnpm typecheck
pnpm test
pnpm build
```

One-command startup smoke checks:

```bash
scripts/kira smoke-dev
scripts/kira smoke-serve
```
