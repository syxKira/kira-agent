# Kira Agent Server

FastAPI backend for Kira Agent local development.

## Local Run

```bash
cd server
uv run uvicorn kira_server.main:app --reload
```

## Real Provider Config

Kira loads real OpenAI-compatible provider config from `~/.kira-agent/config.yaml` by default. Override the path with `KIRA_CONFIG_PATH`.

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
    timeout: 30
    retry:
      attempts: 1
      backoff_seconds: 0.2
```

Do not store real API keys in the project root. Provider metadata returned by the API is redacted, and missing keys fall back to fixture mode so the local web loop still works.

In the web workbench, the primary `Run` action uses provider auto selection and does not force a fixture. Use the explicit `Run fixture` control for deterministic local fixture output.

If you are not using `uv`, create a virtual environment and install the package in editable mode:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn kira_server.main:app --reload
```

## Current Scope

- Health endpoint.
- `POST /api/runs` creates a provider-selected local run and returns `thread_id`, `conversation_id`, `turn_id`, status, fixture/provider metadata, and `events_url`.
- `GET /api/runs/{thread_id}/events` streams Stage 01 SSE events for known runs.
- `POST /api/conversations`, `GET /api/conversations`, `GET /api/conversations/{conversation_id}`, `PATCH /api/conversations/{conversation_id}`, `POST /api/conversations/{conversation_id}/compact`, `POST /api/conversations/{conversation_id}/fork`, `POST /api/conversations/{conversation_id}/rollback`, `GET /api/conversations/{conversation_id}/transcript`, and `GET /api/conversations/{conversation_id}/context` expose local conversation, transcript, Stage 08b compaction state, and Stage 08c branch state.
- Unknown `thread_id` event streams return `404`.
- Provider-neutral event normalization for text/thinking, tool lifecycle, reliability, HITL, done, and error events.
- Deterministic `welcome` and `error` fixtures for tests and local development.
- Real OpenAI-compatible provider streaming when configured.
- Fixture fallback when no valid API key is available.
- `GET /api/provider/status` returns redacted provider readiness metadata.
- `GET /api/tools` returns Stage 02 built-in tool metadata and argument JSON Schemas.
- `GET /api/skills` returns Stage 03 workflow-capable skill metadata.
- `GET /api/skills/{skill_id}` returns skill package details and can load `SKILL.md` body on demand with `include_body=true`.
- `POST /api/project/index/refresh`, `GET /api/project/index/status`, `POST /api/project/search`, and `GET /api/project/file` expose read-only Stage 06 project knowledge APIs with citations.
- `GET /api/runs/{thread_id}/context` returns the redacted ContextItem trace for a run.
- `GET/POST/PUT/DELETE /api/memory`, `POST /api/memory/search`, `POST /api/memory/extract`, candidate decisions, and memory lifecycle actions expose the Stage 07 local memory system.
- `GET /api/runs/{thread_id}/state` returns Stage 04 run state projection.
- `GET /api/runs/{thread_id}/replay` returns read-only replay/debug export.
- `POST /api/runs/{thread_id}/cancel` marks a run cancelled and keeps it inspectable.
- `POST /api/runs/{thread_id}/resume` accepts Stage 05 HITL decisions for interrupted skill graph runs.
- `GET /api/doctor` returns redacted local diagnostics for provider readiness, fixture fallback, SQLite, Python, `rg`, skills, project index, memory, run locks, side-effect ledger, and audit storage.
- `GET /api/audit` lists redacted audit records by thread, conversation, project root, memory ID, action, status, and time bounds.
- `GET /api/runs/{thread_id}/trace`, `GET /api/conversations/{conversation_id}/trace`, `GET /api/project/trace`, and `GET /api/memory/trace` provide bounded read-only trace exports.
- `POST /api/permissions/preview` evaluates the default local permission policy.
- `GET /api/replacements/{replacement_id}/inspect` returns a policy-gated, redacted replacement inspection response or a structured denial.
- LangChain Core-compatible built-in tools for read-only local file context, controlled Python execution, and `ask_user_question`.
- Skill-selected runs can execute a minimal LangGraph `StateGraph` workflow and dispatch Stage 02 tools through `ToolNode`.
- Skill package discovery reads local `SKILL.md` frontmatter and optional `skill.yaml` manifests from bundled, user-local, project-local, and `KIRA_SKILL_PATHS` roots.
- Project knowledge indexing stores metadata and chunks in Kira-owned SQLite storage only; project files remain read-only.

## Stage 01 Boundaries

Run state is process-local and intentionally not durable. Checkpointing, resume, run locks, replay, idempotency, side-effect ledgers, retrieval, memory, and LangGraph runtime are deferred to later roadmap stages.

## Stage 02 Boundaries

Stage 02 tools do not dispatch LangGraph nodes, build retrieval indexes, mutate project files, invoke a general shell, persist audit records, or add HITL resume UI. File tools are read-only. `run_python_script` runs Python through argv-only subprocess execution with cwd, environment, timeout, and output controls.

## Stage 03 Boundaries

Stage 03 graph execution is opt-in through `skill_id` and process-local. It does not add SQLite checkpointing, durable resume, replay, run locks, idempotency, side-effect ledgers, HITL interrupt UI, memory, project knowledge retrieval indexes, full skill packaging, or business-specific workflows. Graph state and skill metadata only receive redacted provider metadata.

## Stage 04 Boundaries

Stage 04 stores local graph reliability records in SQLite. The default path is `~/.kira-agent/kira.db`; override with `KIRA_RUNTIME_DB_PATH` for tests or isolated local runs. Runtime records include persisted KiraEvents, state projections, run attempts, provider attempts, run locks, checkpoint summaries, side-effect ledger summaries, and repair notes.

Stage 04 does not add full HITL approval/edit UI, project knowledge retrieval, memory, production multi-user storage, cloud sync, distributed workers, a general shell, or project file mutation tools. Replay is read-only by default and must not re-run tools, providers, or side effects.

## Stage 05 Boundaries

Stage 05 adds local HITL interrupt/resume behavior for checkpointed skill graph runs. A graph can emit a redacted `interrupt` event, the frontend can post a validated resume decision to `POST /api/runs/{thread_id}/resume`, and the backend persists a `resume` event plus continuation events on the same `thread_id`. SSE reconnect uses `after_seq` to replay missed persisted events without re-running graph work.

The deterministic fixture skill is `stage-05-hitl-fixture-skill`. Prompts containing `edit`, `question`, or `python` select those interrupt kinds; other prompts use approval. Fixture-only HITL tests do not require real API keys.

Stage 05 does not add project knowledge retrieval, memory, remembered approvals, multi-reviewer workflows, remote auth, a general shell, or project file mutation tools.

## Stage 06 Skill Packages And Project Knowledge

Every local skill package must contain `SKILL.md` with frontmatter:

```markdown
---
name: Example Skill
description: When this skill should be considered
---

Detailed skill instructions load only after explicit activation or detail request.
```

Workflow-capable packages can add `skill.yaml`:

```yaml
workflows:
  - name: example-workflow
    description: Runs the model with package context
model_hint:
  profile: minimax-global
permissions:
  tools:
    - list_project_files
fixtures:
  - name: local-fixture
```

Skill manifests may reference configured provider profiles or models, but they must not contain API keys, authorization headers, raw provider configs, or custom base URLs. Effective permissions can narrow Kira core policy only; they cannot add shell access or project mutation.

Project knowledge refresh uses Stage 02 file policy for root resolution, ignored paths, binary detection, large-file caps, and symlink containment. Retrieval combines indexed chunks and live lexical search, returns citations with project-relative paths and line ranges, and marks changed indexed content as stale.

Runs may include `skill_id`, `project_context_query`, `project_context_limit`, and `context_budget`. The provider receives packed ContextItems, and `/api/runs/{thread_id}/context` explains which skill/project context was included, truncated, or omitted. Retrieved project text is always labeled as untrusted project data.

## Stage 07 Memory

Memory records are stored only in Kira-owned SQLite tables. The backend supports typed/scoped records, deterministic lexical retrieval, score explanations, dedupe metadata, memory citations, tombstones, lifecycle events, dry-run extraction candidates, and candidate approve/reject/edit/defer decisions.

Run creation can opt into retrieval with `include_memory`, `memory_query`, `memory_scopes`, `memory_types`, and `memory_top_k`. Retrieved memories are converted to `ContextItem(kind="memory")` before provider input assembly; raw prompt concatenation is not used for memory injection. Replay and state projection expose saved memory summaries without creating new retrievals, citations, candidates, provider calls, tools, or lifecycle actions.

The memory guard blocks and redacts secrets, raw provider config, unredacted provider failures, and high-risk personal/customer data before persistence. Blocked writes and candidates do not store the rejected raw text.

## Stage 08a Transcript Core

`conversation_id` is the local multi-turn continuity key. `thread_id` remains the run execution key used by SSE, replay, cancellation, locks, and HITL resume. A follow-up run should pass the prior `conversation_id`; the backend creates a new turn and thread while reusing eligible visible transcript history.

Run creation persists the user transcript message before provider, graph, project retrieval, or memory retrieval work starts. Visible assistant `text_delta` chunks are stored as transcript text parts. `thinking_delta` content is not stored as visible transcript and is not used as future conversation history.

Conversation history is converted into bounded `ContextItem(kind="conversation_history")` records before provider input assembly. Tool/HITL/error markers are persisted only as compact transcript parts. Transcript records remain separate from Stage 07 memory; no memory record is created automatically from a completed transcript turn.

## Stage 08b Context Compaction

Compaction summaries are explicit SQLite records linked to source message IDs, source hashes, tail boundaries, token estimates, stale status, and summarizer metadata. Source transcript messages remain readable. The compact API uses deterministic fixture summarization by default; explicit real-provider summarization is attempted only when the existing provider config is valid, and provider metadata is redacted.

Run creation can perform overflow compaction before assembling provider input. The policy is controlled by raw message count, estimated token/character limits, and context budget pressure. If compaction fails, the backend records a redacted overflow error in the transcript trace and falls back to bounded recent history.

### Stage 08c Fork/Rollback

Fork accepts `source_message_id` or `source_turn_id` and returns a new conversation plus a redacted branch record and active-head transition. The new conversation active head points at the source message, so context includes inherited source history only up to the fork point and then fork-local turns.

Rollback accepts `target_message_id` or `target_turn_id` and moves the selected conversation active head to that target. It records previous/new heads and inactive message IDs without deleting messages, compacting history, calling a provider, running tools, or creating memory records. Transcript reads label messages as `active`, `inactive`, or `inherited`; context traces include `inactive_branch` omissions.

Resume checks the interrupted turn against the current active chain. If the turn is now inactive, `POST /api/runs/{thread_id}/resume` returns `409` with `inactive_branch_conflict` metadata instead of creating a continuation on an abandoned branch.

Oversized or sensitive tool outputs are stored as replacement records and provider-facing stubs. Public APIs expose only summary text, hashes, omitted counts, reason, retention policy, status, and redacted references. There is no Stage 08b raw blob resolution API, and state/replay export saved metadata without regenerating summaries or resolving blobs.

## Stage 09 Safety And Observability

Stage 09 adds a local permission/audit/diagnostics layer around the existing Stage 01-08 flows. Audit writes are non-critical: if audit storage fails, the server records a doctor diagnostic and keeps the local web loop running.

Default policy decisions are deterministic and do not require network access. Provider/model overrides, skill activation, controlled Python execution, memory writes, transcript lifecycle actions, workflow external actions, and replacement inspection receive explicit permission decisions and audit metadata. Unknown provider overrides and invalid replacement inspection are denied; risky local actions can return approval-required `ask` decisions.

Smoke commands:

```bash
cd server
uv run --extra dev pytest
curl http://127.0.0.1:8000/api/doctor
curl 'http://127.0.0.1:8000/api/audit?limit=20'
```
