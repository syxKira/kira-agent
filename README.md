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

Start the backend:

```bash
cd server
uv run uvicorn kira_server.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend:

```bash
cd web
pnpm install
pnpm dev
```

Open:

```text
http://127.0.0.1:5173/
```

By default, the frontend talks to `http://127.0.0.1:8000`. To override it:

```bash
cd web
VITE_KIRA_API_BASE=http://127.0.0.1:8000 pnpm dev
```

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
