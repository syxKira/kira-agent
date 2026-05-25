# Kira Agent Roadmap

Kira Agent is a general local agent built around a Python backend, a TypeScript frontend, and a skill-driven graph runtime. It inherits Kai's reusable agent foundations: provider abstraction, fixture replay, streaming event discipline, thinking separation, tool protocol, HITL, checkpoint/replay, ContextItem budgeting, skills, memory, permissions, audit, diagnostics, and project-local read-only retrieval, then matures retrieval into a cited project knowledge system.

Kira deliberately does not inherit Kai's code-agent-specific surface: CLI/TUI/Ink as the main UI, coding profile, write/edit/apply_patch, patch safety, LSP diagnostics, git-diff workflows, or hardened bash. The only execution tool in v0 is controlled Python script execution.

## Stage Overview

| Stage | Name | Capability | Exit Signal |
| ---: | --- | --- | --- |
| 01 | Local Web Foundation | FastAPI + Vite React local app, welcome screen, run workbench, provider/fixture, SSE shell | Welcome screen can enter a timeline-style agent workspace and stream fixture events |
| 02 | Tool Protocol + Local Context | LangChain Core tools, read-only project file tools, controlled Python execution | Tool schemas are visible through API and validated in tests |
| 03 | Skill-driven LangGraph Runtime | Core graph runtime loads workflows from skills | A test skill graph runs through StateGraph and ToolNode without hardcoded business nodes |
| 04 | Reliable Graph Runtime + Replay | SQLite checkpointer, thread_id resume, idempotency, retries, run locks, side-effect ledger | A failed or interrupted run can resume without duplicating completed work |
| 05 | HITL + SSE Streaming | interrupt + astream_events mapped to frontend timeline and prompt panels | Frontend can approve/edit an interrupt and resume the same run |
| 06 | Skill Package Contract + Project Knowledge | Complete skill package contract, project knowledge index/retriever, workflow/tool/context/UI metadata, ContextItem injection | Skills and project retrieval inject bounded, cited ContextItems |
| 07 | Memory System | Typed/scoped memory, retrieval explain, citations, extraction dry-run, lifecycle | The frontend can show why a memory was injected and users can manage it |
| 08 | Transcript + Conversation Context | Persistent conversations, parent-linked transcript, explicit compaction, tool-output replacement, fork/rollback, follow-up context | A follow-up prompt uses the active parent chain, summaries, and bounded tool context without copying context manually |
| 09 | Safety + Observability + Polish | file/retrieval/Python/graph/skill/memory/transcript boundaries, audit, diagnostics, local packaging | Local install has doctor checks, audit export, and core regression coverage |
| 10 | Web Experience Refinement | Dark single-agent welcome, task rail, polished timeline, composer, visual smoke tests | Kira feels like a finished local Web Agent product |
| 11 | Frontend Chat Experience Hardening | cis-mira-informed chat UX pass: centered Chinese welcome, collapsible `思考过程`, inline tool activity, clear composer, no default right inspector | Kira feels like a focused professional data-agent assistant rather than an operator dashboard |
| 12 | Mira Frontend Study + Contract | Structured cis-mira frontend study, Kira target UI spec, dependency policy for useful UX libraries | Frontend agents have concrete study docs before rebuilding the chat UI |
| 13 | Chat Event Aggregation | Frontend turn view-model layer that merges transcript and live SSE events into coherent conversation turns | One prompt renders one assistant answer even with interleaved thinking/tool/status/done events |
| 14 | Mira-like Chat UI | Light conversation-first UI with right user bubbles, assistant identity, collapsed thinking, inline tools, quiet composer | Kira's default web UI resembles a real data-agent chat product rather than an event log |
| 15 | Visual Parity + Regression | Browser screenshot smoke and DOM checks for Mira-like chat states | Regressions such as scattered answers, loud Completed cards, default inspector, and input residue fail locally |

## Capability Curve

| Stages | Capability Curve |
| --- | --- |
| 01-02 | Establish local web loop and safe tools before adding graph complexity |
| 03-04 | Add skill-defined workflow orchestration, then make it durable, idempotent, resumable, and replayable |
| 05 | Put human decisions and token/tool streaming on the same event contract |
| 06 | Make skills real packages and upgrade local file tools into a cited project knowledge retrieval system |
| 07 | Add durable memory with scope, type, citations, lifecycle, extraction dry-run, and Web inspection |
| 08 | Add conversation-level transcript, active parent chain, compaction, and branch/rollback semantics so separate runs become coherent multi-turn sessions |
| 09 | Turn the prototype into a dependable local agent with boundaries, audit, and diagnostics |
| 10 | Refine the user-facing Web experience after the runtime behavior is stable |
| 11 | Harden the chat experience based on hands-on review and cis-mira references |
| 12-15 | Replace the remaining event-workbench frontend shape with a studied, turn-based, Mira-like conversation product and lock it with visual regression |

## Architecture Overview

Kira has seven layers:

| Layer | Responsibility |
| --- | --- |
| `frontend` | Vite React welcome screen and timeline-style workbench for runs, events, state, skills, tools, and HITL prompts |
| `api` | FastAPI routes, SSE, resume endpoint, redacted provider status, tools/skills metadata, static local dev integration |
| `agent_core` | provider config/selection, provider adapters, event normalization, transcript-aware ContextItem builder, run orchestration |
| `tooling` | LangChain Core `BaseTool` tools, controlled Python execution, read-only project file tools |
| `retrieval` | project file inventory, chunking, lexical/FTS retrieval, citation packing, stale-source detection |
| `graph_runtime` | LangGraph `StateGraph`, `ToolNode`, conditional edges, checkpointer, skill workflow loader, reliable execution guardrails |
| `storage` | SQLite checkpoints, run locks, side-effect ledger, conversations, transcript, project index, session projections, audit records, memory records, debug traces |

See [`architecture/final-architecture.md`](architecture/final-architecture.md) for the target shape, [`architecture/frontend-experience.md`](architecture/frontend-experience.md) for the product UI plan, [`../docs/mira-frontend-study/README.md`](../docs/mira-frontend-study/README.md) for the cis-mira frontend study, [`appendix/graph-runtime-reliability.md`](appendix/graph-runtime-reliability.md) for graph reliability rules, [`appendix/project-knowledge-retrieval.md`](appendix/project-knowledge-retrieval.md) for local retrieval system design, [`appendix/skill-contract.md`](appendix/skill-contract.md) for the skill package contract, [`appendix/memory-model.md`](appendix/memory-model.md) for memory rules, and [`appendix/transcript-conversation-context.md`](appendix/transcript-conversation-context.md) for transcript continuity rules.

## Important Boundaries

- Kira core does not ship a built-in `planner -> gen_data -> send_kafka -> wait_ds -> reflect` workflow. That shape can be declared by a skill later.
- Project-local file tools are read-only context tools. They never write, move, delete, patch, or stage files.
- The project knowledge system may index and cite local files, but index writes go only to Kira's own SQLite/cache storage and never mutate project files.
- Transcript is conversation-scoped short-term context. It is not memory, not graph checkpoint state, and not hidden thinking. Context is built from the active parent chain plus explicit compaction summaries and bounded tool summaries.
- Python execution is controlled: bounded cwd, allowed env, timeout, output caps, audit, and optional HITL approval for risky scripts.
- Real provider config is user-local and redacted. Later stages consume selected provider/model metadata and normalized KiraEvents; they never read raw API keys.
- LangChain is limited to `langchain-core` tool primitives. Kira does not use LangChain agents, chains, memory, or prompt templates.
- LangGraph is limited to graph orchestration, ToolNode dispatch, checkpointer, interrupt, and event streaming. Kira's own runtime layer adds run locks, idempotency keys, side-effect ledger, retry policy, and replay semantics around those primitives.

## Cross-stage Test Plan

| Area | Required Coverage |
| --- | --- |
| Provider selection | default config, request override, skill hint, fixture fallback, timeout/retry, stream mapping, redaction |
| Tool protocol | `@tool` / `BaseTool` schema generation, validation, error formatting, ToolNode dispatch |
| Local file tools | path escape, symlink escape, ignore rules, binary/large files, truncation, no-`rg` fallback |
| Project retrieval | inventory refresh, chunk IDs, FTS/live search, citations, stale markers, omitted snippets, adversarial local files |
| Graph reliability | duplicate resume, stale lock, retryable timeout, non-retryable failure, side-effect reuse, cancellation, corrupted checkpoint |
| HITL/SSE | interrupt event, resume value validation, SSE reconnect by event sequence, token/tool/checkpoint ordering |
| Skill workflow | declarative/factory workflow validation, ToolNode tool allowlist, reliability hints, fixture replay |
| Memory | retrieval explain, citation records, extraction dry-run, secret guard, lifecycle actions |
| Transcript | conversation isolation, active parent chain, follow-up context, explicit compaction, fork/rollback, replacement stubs, hidden-thinking exclusion, bounded tool summaries |
| Python execution | cwd/env boundary, timeout, output caps, approval denied, audit record |

## How To Use This Roadmap

Start with Stage 01 and keep every stage independently reviewable. Each stage should produce a local demo, fixture tests, and a small set of acceptance checks before the next stage starts. When a new business workflow appears, model it as a skill first; do not add it directly to core. Treat Stage 10 and Stage 11 as the first web polish passes, then use Stage 12-15 as the main frontend rebuild sequence for the Mira-like conversation experience.
