# Kira Agent

Kira Agent is planned as a general local agent, not a code-specialized agent. It uses a Python backend and a TypeScript frontend, starts with local development and debugging, and keeps the reusable agent foundations from Kai while removing code-editing capabilities.

The roadmap lives in [`kira-agent-roadmap/README.md`](kira-agent-roadmap/README.md). It is the control surface for staged implementation.

Project-level instructions for coding agents live in [`AGENTS.md`](AGENTS.md). Read it before applying a stage or OpenSpec change.

## Development Layout

```text
kira-agent/
  AGENTS.md # Project instructions for coding agents
  server/   # FastAPI backend, Python src layout
  web/      # Vite React frontend
  src/      # Shared schemas/contracts
  scripts/  # Local helper scripts
```

## Local Development

Start the server:

```bash
cd server
uv run uvicorn kira_server.main:app --reload
```

Start the web app:

```bash
cd web
pnpm install
pnpm dev
```

Open `http://localhost:5173`, click Start, and use `Run` to send the prompt through provider auto selection. If a valid real provider is configured, this streams the real model; otherwise the backend falls back to fixture mode and shows the fallback reason in provider metadata. Use `Run fixture` for the deterministic welcome fixture.

The default frontend API base is `http://127.0.0.1:8000`. Override it when needed:

```bash
cd web
VITE_KIRA_API_BASE=http://127.0.0.1:8000 pnpm dev
```

## Current Scope

- Python backend with FastAPI.
- TypeScript frontend with Vite React.
- Shared Stage 01 run and event contracts in `src/`.
- OpenAI-compatible provider boundary and deterministic fixture provider.
- Real OpenAI-compatible provider streaming when configured through `~/.kira-agent/config.yaml` or `KIRA_CONFIG_PATH`.
- Fixture fallback when no valid API key is available.
- `POST /api/runs` for in-memory provider-selected local runs with fixture fallback.
- `GET /api/runs/{thread_id}/events` for SSE event streaming.
- `conversation_id` continuity, transcript persistence, and conversation APIs for local multi-turn runs.
- Conversation fork/rollback APIs for local transcript branching without deleting abandoned transcript rows.
- `GET /api/tools` for Stage 02 built-in tool schemas.
- `GET /api/skills` for Stage 03 workflow-capable skill metadata.
- `GET /api/skills/{skill_id}` for Stage 06 skill package details loaded on demand.
- `POST /api/skills/install` for project-local zip skill installation into `.kira/skills`.
- `POST /api/project/index/refresh`, `GET /api/project/index/status`, `POST /api/project/search`, and `GET /api/project/file` for read-only project knowledge indexing and cited retrieval.
- `GET /api/runs/{thread_id}/context` for included/truncated/omitted run ContextItems.
- `GET/POST/PUT/DELETE /api/memory`, `POST /api/memory/search`, memory lifecycle actions, and extraction candidate review for the local Stage 07 memory system.
- `GET /api/runs/{thread_id}/state` and `GET /api/runs/{thread_id}/replay` for Stage 04 state projection and replay.
- `GET /api/doctor`, `GET /api/audit`, `GET /api/runs/{thread_id}/trace`, conversation/project/memory trace endpoints, permission preview, and replacement inspection policy for Stage 09 safety/observability.
- `POST /api/runs/{thread_id}/resume` for Stage 05 HITL decisions on interrupted skill graph runs.
- LangChain Core-compatible built-in tool registry.
- Skill-driven LangGraph runtime for opt-in workflow runs.
- SQLite-backed local reliability records for graph events, attempts, provider attempts, run locks, checkpoints, and side-effect ledger summaries.
- Read-only project file tools for listing, search, and bounded reads.
- Controlled Python script execution through a Python subprocess with cwd/env/timeout/output caps.
- Controlled shell command execution for project-bound local runs with cwd/env/timeout/output caps and redaction.
- `ask_user_question` with Stage 05 graph-context HITL behavior and structured non-interactive fallback.
- Welcome screen and timeline-style run workbench.
- The primary workbench `Run` action uses `provider_mode: "auto"`; deterministic fixtures are available through explicit fixture controls.
- HITL timeline rows and approval/edit/question/Python approval panel for the Stage 05 fixture workflow.
- Skill package catalog/detail controls, project knowledge search/index/context inspector panels, and local memory inspector controls.
- Hidden thinking is emitted as `thinking_delta` and is not rendered as normal assistant answer text.

## Stage 01 Event Contract

Every SSE message carries a normalized event:

```json
{
  "type": "text_delta",
  "thread_id": "local-example",
  "seq": 1,
  "data": {
    "text": "Visible assistant text"
  }
}
```

Core event types include:

- `text_delta`: visible assistant text or clearly labeled fixture preview data.
- `thinking_delta`: hidden thinking/status metadata; never normal answer text.
- `tool_start` and `tool_result`: bounded tool lifecycle data.
- `retry`, `checkpoint`, and `side_effect_reused`: reliability markers.
- `interrupt` and `resume`: Stage 05 HITL pause and continuation markers.
- `done`: terminal success event.
- `error`: terminal failure event.

## Stage 02 Tool Boundary

Stage 02 adds tool schemas and local context primitives only. It does not add LangGraph graph dispatch, LangChain agents/chains/memory, retrieval indexes or citations, checkpoint/resume, memory, production auth, frontend HITL approval UI, file mutation tools, or unbounded shell execution.

Built-in tools:

- `list_project_files`
- `search_project_files`
- `read_project_file`
- `run_python_script`
- `run_shell_command`
- `ask_user_question`

## Stage 03 Graph Boundary

Stage 03 adds a minimal skill-driven LangGraph runtime. A workflow-capable skill can provide a generic graph that runs through `StateGraph`, dispatches Stage 02 tools through `ToolNode`, and streams normalized Kira events.

Stage 03 does not add SQLite checkpointing, durable resume, run locks, replay, side-effect ledgers, HITL interrupt UI, memory, project knowledge retrieval indexes, a full skill package contract, or built-in business workflows.

## Stage 04 Reliability Boundary

Stage 04 adds local SQLite runtime reliability around graph runs: persisted KiraEvents, state projection, replay/debug export, run attempts, provider attempts, run locks, cancellation, checkpoint summaries, repair notes, and side-effect ledger summaries. The default runtime database path is `~/.kira-agent/kira.db`; tests can override it with `KIRA_RUNTIME_DB_PATH`.

Stage 04 does not add the Stage 05 HITL approval UI, Stage 06 project knowledge retrieval, Stage 07 memory, production multi-user storage, distributed workers, unbounded shell, or project mutation tools.

## Stage 05 HITL Boundary

Stage 05 adds local human-in-the-loop event streaming for checkpointed skill graph runs. Interrupts are persisted as normalized `interrupt` events, resume decisions are posted to `POST /api/runs/{thread_id}/resume`, and replay/state APIs expose only redacted pending interrupt summaries. The built-in `stage-05-hitl-fixture-skill` can exercise approval, rejection, edit, question, and Python approval paths without a real API key.

Stage 05 does not add project knowledge retrieval, memory, remembered permission policy, multi-reviewer workflows, notifications, remote auth, unbounded shell, or project file mutation tools.

## Stage 06 Skill And Project Context Boundary

Stage 06 adds local skill packages and read-only project knowledge retrieval. A skill package requires `SKILL.md` frontmatter with `name` and `description`; optional `skill.yaml` can declare workflows, permissions, fixtures, context hints, and provider profile/model hints. Full skill docs are loaded progressively only after detail request or explicit activation.

Project knowledge indexing writes only to Kira-owned SQLite storage. It reuses the Stage 02 read-only file policy for project roots, ignored paths, symlink escapes, binary files, and large-file caps. Retrieval returns cited snippets with path, line/chunk metadata, stale markers, and omission counts.

Runs can opt into skill context with `skill_id`. Project-bound default-agent runs expose read-only project search/read tools so the model can retrieve local business documents only when the task needs them, similar to Codex's on-demand tool use. Callers can still pre-inject bounded project context with `project_context_query` or explicitly set `auto_project_context: true` for prompt-derived retrieval. Context is packed as typed ContextItems before provider input, and retrieved project text is labeled as untrusted data so it cannot grant permissions or alter provider secrets/config.

## Stage 07 Memory Boundary

Stage 07 adds a local typed memory system backed by Kira-owned SQLite storage. Memory records have explicit scopes (`session`, `projectLocal`, `project`, `user`), types, status, source metadata, confidence, tags, optional expiry, lifecycle events, tombstones, retrieval traces, and memory citations.

Runs opt into memory retrieval with `include_memory`, `memory_query`, `memory_scopes`, `memory_types`, and `memory_top_k`. Selected memories enter provider input only as `ContextItem(kind: "memory")`, remain distinct from project citations, and are shown in `/api/runs/{thread_id}/context`, state, and replay summaries without rerunning retrieval.

The memory guard rejects API keys, bearer tokens, cookies, private keys, `.env` secrets, raw provider config, unredacted provider errors, and high-risk personal/customer data. Rejected raw text is not persisted in memory records, events, candidates, diagnostics, replay, or frontend responses.

Extraction is dry-run by default and produces reviewable candidates. Active memory records are created only after explicit approval or manual write. Stage 07 does not add a vector database, cloud sync, long-term autonomous memory policy, remembered permissions, production auth, project mutation tools, or unbounded shell.

## Stage 08a Transcript Boundary

Stage 08a adds the core local transcript system. `conversation_id` is the multi-turn continuity cursor used by the workbench and run API, while `thread_id` remains the execution/replay/resume cursor for one run lineage. A conversation can contain many turns and thread IDs; a thread does not mean a chat session.

Run creation accepts optional `conversation_id`, creates a conversation when omitted, persists the user message before execution, returns `conversation_id` and `turn_id`, and stores visible assistant `text_delta` output as transcript parts. Hidden `thinking_delta` output is not restored as assistant answer text and is not injected into future conversation history.

Conversation history is packed into provider input as `ContextItem(kind: "conversation_history")` and remains separate from Stage 07 memory. Transcript completion does not automatically create memory records.

Conversation APIs:

- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{conversation_id}`
- `PATCH /api/conversations/{conversation_id}`
- `POST /api/conversations/{conversation_id}/compact`
- `POST /api/conversations/{conversation_id}/fork`
- `POST /api/conversations/{conversation_id}/rollback`
- `GET /api/conversations/{conversation_id}/transcript`
- `GET /api/conversations/{conversation_id}/context`

## Stage 08b Context Compaction Boundary

Stage 08b adds explicit local compaction records and tool-output replacement stubs on top of Stage 08a transcript storage. Manual compaction uses `POST /api/conversations/{conversation_id}/compact`; fixture summarization is the default, while `summarizer_mode: "real"` is allowed only when an existing real provider config is valid and remains redacted.

Run creation can trigger overflow compaction when enabled. The overflow policy is configurable with combined raw message, estimated token/character, and context budget pressure thresholds. Compaction creates inspectable summary metadata and never deletes source transcript messages.

Large or sensitive tool outputs are replaced with bounded model-visible stubs containing a summary, reason, omitted character count, hash, retention policy, and redacted reference metadata. Stage 08b APIs do not expose raw replacement blobs or add a blob-resolution endpoint; replay/state/context responses stay read-only and frontend-safe.

## Stage 08c Fork And Rollback Boundary

Stage 08c adds local transcript branching. `POST /api/conversations/{conversation_id}/fork` creates a new conversation whose active head points at a valid source message or turn on the current active chain. The fork inherits history only through that source point; later source-conversation turns are not injected into fork context.

`POST /api/conversations/{conversation_id}/rollback` moves the selected conversation active head back to a valid active-chain message or turn. It records the previous head, new head, reason metadata, and inactive message IDs, but it does not delete transcript rows, create memory records, call providers, run tools, compact history, or mutate replay data.

New runs after rollback parent from the rollback head. Context traces include active-head and branch metadata plus omitted inactive-branch records. HITL resume rejects interrupted runs whose turn has fallen off the active branch with `inactive_branch_conflict`; same-branch resume still continues the same `thread_id`.

## Real LLM Provider Config

Provider secrets live outside the repo by default:

```text
~/.kira-agent/config.yaml
```

Override the path with `KIRA_CONFIG_PATH`. Example:

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

API keys are redacted from API responses, diagnostics, and frontend provider readiness metadata. Do not commit real keys to this project.

## Safety And Observability

Stage 09 keeps the local loop inspectable without adding shell access or project mutation tools:

- `GET /api/doctor` reports redacted local readiness for provider config, fixture fallback, SQLite runtime storage, Python, `rg`, skills, project index, memory, run locks, side-effect ledger, and audit storage.
- `GET /api/audit` lists redacted audit records and supports filters such as `thread_id`, `conversation_id`, `project_root`, `memory_id`, `action`, `status`, `since`, `until`, and `limit`.
- `GET /api/runs/{thread_id}/trace`, `GET /api/conversations/{conversation_id}/trace`, `GET /api/project/trace`, and `GET /api/memory/trace` export bounded read-only traces. These calls do not rerun providers, tools, retrieval, memory writes, or transcript operations.
- `POST /api/permissions/preview` evaluates the local default permission policy and returns redacted `allow`, `ask`, or `deny` decisions.
- `GET /api/replacements/{replacement_id}/inspect` is permission-gated and returns only redacted inspection metadata unless local policy allows the retained replacement content.

The web workbench Safety panel exposes doctor checks, audit records, trace exports, and replacement inspection errors in the existing inspector layout.

## Non-goals

- No CLI/TUI/Ink primary experience.
- No code-agent build profile.
- No write/edit/apply_patch tools.
- No git diff, LSP, diagnostics, or patch safety flows.
- No unbounded or interactive shell.
- No built-in business workflow hardcoded into core; workflows come from skills.
- No production auth, remote deployment, project mutation tools, cloud memory sync, vector database, or unbounded shell in the current local foundation.
