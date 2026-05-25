## Why

Kira can now load skills and retrieve cited project context, but it still cannot remember durable preferences, decisions, workflow lessons, or useful facts across runs. Stage 07 adds a local memory system so remembered context is typed, scoped, cited, explainable, removable, and injected through the same ContextItem budget path as skills and project knowledge.

## What Changes

- Add durable local memory records with scopes `session`, `projectLocal`, `project`, and `user`.
- Add memory types `preference`, `feedback`, `decision`, `project`, `reference`, `fact`, and `workflow`, with statuses `active`, `stale`, and `archived`.
- Add manual memory CRUD APIs and frontend memory inspector for list, search, add, edit, archive, delete, merge, refresh, stale, and promote operations.
- Add explainable memory retrieval with top-k limits, budget limits, deterministic scoring, dedupe, score reasons, and retrieval explanations.
- Inject active memory only as budgeted `ContextItem(kind="memory")` records with citations and omission/truncation traces.
- Add memory citation/event storage so every injected memory is traceable to source and run usage.
- Add post-run extraction dry-run that proposes `MemoryCandidate[]` from completed runs without writing automatically.
- Add deterministic fixture/mock extraction path for tests and no-key local runs; use real provider only when configured and explicitly available.
- Add secret/sensitive guard before all memory writes and candidates, covering API keys, tokens, cookies, private keys, `.env` values, raw provider config, and unredacted upstream errors.
- Keep Stage 07 focused: no vector DB, no cloud/team sync, no Stage 08 audit/doctor/export polish, no general shell, and no project file mutation.

## Capabilities

### New Capabilities

- `memory-record-contract`: Defines memory records, scopes, types, statuses, source metadata, confidence, tags, tombstones, events, write validation, and secret guard.
- `memory-retrieval-context`: Defines deterministic memory retrieval, ranking, dedupe, explanations, citations, ContextItem conversion, budget handling, and run integration.
- `memory-extraction-dry-run`: Defines post-run memory candidate extraction, deterministic fixture extraction, real-provider extraction fallback rules, candidate risk/secret filtering, and no automatic writes by default.
- `memory-lifecycle`: Defines lifecycle operations for archive, delete, merge, refresh, stale, promote, approval requirements, and tombstone/event records.
- `memory-inspector-ui`: Defines frontend memory inspector behavior for listing, searching, explaining, adding, reviewing candidates, and lifecycle actions.

### Modified Capabilities

- `context-item-budgeting`: Add memory ContextItems, memory citations, and memory omission/truncation trace behavior.
- `local-run-api`: Add memory retrieval controls to run creation and expose memory items/citations in run context traces.
- `durable-run-storage`: Add SQLite memory tables for records, citations, events, tombstones, retrieval traces, and extraction candidates.
- `run-state-replay`: Add redacted memory injection/candidate summaries to state and replay/debug exports.
- `timeline-hitl-ui`: Allow memory write/promotion approval interrupts to reuse the Stage 05 HITL surface when policy requires human approval.

## Impact

- Backend: memory schemas/models, SQLite migrations, memory repository, retrieval scorer, ContextItem adapter, extraction dry-run service, secret guard, lifecycle service, run integration, and memory APIs.
- Frontend: memory inspector panel, search/explain views, add/edit form, candidate review surface, lifecycle actions, and run context display for memory citations.
- Shared contracts: memory record, memory candidate, memory citation, memory retrieval explanation, memory action, memory API, and extended ContextItem schemas.
- Storage: Kira-owned SQLite tables for memory records, citations, events, tombstones, retrieval traces, and extraction candidates; no project-root writes.
- Tests: deterministic retrieval ranking, secret blocking, fixture extraction, no-key behavior, lifecycle transitions, citation creation, ContextItem budget traces, API redaction, UI rendering, and Stage 01-06 regression checks.

## Scope

- Local durable memory only.
- Manual memory CRUD and lifecycle operations.
- Explainable lexical retrieval only.
- Post-run extraction dry-run only.
- HITL approval only for policy-required memory writes/promotions.
- Fixture/mock extraction that runs without a real API key by default.

## Non-goals

- No vector database, embeddings, semantic/hybrid ranking, or external memory service.
- No cloud/team sync, remote memory marketplace, or shared multi-user permissions.
- No automatic writes to `project` or `user` scope without policy/HITL approval.
- No Stage 08 audit log, doctor checks, broad trace export, remembered permission policy, or packaging polish.
- No Stage 09 visual redesign.
- No arbitrary shell tool and no project file write/edit/delete/patch/stage tools.

## Acceptance Criteria

- Manual add/list/search/read/update/archive/delete works through `/api/memory` without requiring a real API key.
- Memory records validate scope, type, status, confidence, tags, source metadata, and redacted payloads.
- Secret guard blocks API keys, tokens, cookies, private keys, `.env` values, raw provider config, and unredacted provider errors before persistence.
- Retrieval returns deterministic ranked results with score reasons, dedupe metadata, top-k limits, and omission counts.
- Active memories can be injected into runs only as budgeted `ContextItem(kind="memory")` records.
- Every injected memory creates a memory citation visible in run context trace and replay/debug summaries.
- Archived, deleted, stale, expired, or out-of-scope memories are not injected by default.
- Extraction dry-run produces candidates and explanations without writing records automatically.
- Fixture/mock extraction tests pass without real API keys; real smoke tests are skipped unless provider config is present.
- Frontend memory inspector shows records, search explanations, citations, candidates, and lifecycle actions without exposing secrets.

## Risks

- Memory can store wrong or temporary facts; Stage 07 must default to manual writes and dry-run extraction.
- Memory can leak secrets if guard coverage is weak; tests must include realistic key/token/private-key fixtures.
- Retrieval can over-inject stale or low-value context; ranking, scope filtering, statuses, top-k, and budget traces must be explicit.
- UI can make memory feel automatic or hidden; the inspector must show why memory was used and make removal/lifecycle operations direct.
