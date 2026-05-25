## 1. Shared Contracts And Storage

- [x] 1.1 Add shared schema definitions for memory records, scopes, types, statuses, sources, tags, confidence, timestamps, expiration, and frontend-safe public metadata.
- [x] 1.2 Add shared schema definitions for memory events, citations, tombstones, retrieval explanations, score reasons, extraction candidates, guard results, and lifecycle actions.
- [x] 1.3 Extend shared ContextItem schemas to include `memory` kind and memory citation metadata while preserving Stage 06 project citation metadata.
- [x] 1.4 Export TypeScript types for memory records, candidates, citations, retrieval responses, lifecycle actions, and run memory context from `src/`/`web`.
- [x] 1.5 Add SQLite migrations for memory records, memory events, memory citations, tombstones, retrieval traces, extraction candidates, and candidate decisions.
- [x] 1.6 Add migration tests proving Stage 04-06 runtime/project/context tables are preserved after Stage 07 migrations.
- [x] 1.7 Add contract tests validating representative memory records, retrieval responses, candidates, actions, citations, and context traces against shared schemas.

## 2. Memory Validation And Secret Guard

- [x] 2.1 Implement backend memory models for record create/update payloads, source metadata, public responses, events, citations, tombstones, and action requests.
- [x] 2.2 Implement validation for allowed scopes `session`, `projectLocal`, `project`, and `user`.
- [x] 2.3 Implement validation for allowed memory types `preference`, `feedback`, `decision`, `project`, `reference`, `fact`, and `workflow`.
- [x] 2.4 Implement validation for statuses `active`, `stale`, and `archived`, including expiry handling for non-injectable memories.
- [x] 2.5 Implement secret/sensitive guard patterns for API keys, bearer tokens, cookies, private keys, `.env` values, raw provider config, unredacted provider errors, and high-risk personal/customer data.
- [x] 2.6 Ensure rejected memory writes do not persist raw rejected text in records, events, candidates, diagnostics, logs, replay, or frontend responses.
- [x] 2.7 Add tests for valid memory writes, invalid shape rejection, secret blocking, redaction, expiry, and no-persistence of rejected secret fixtures.

## 3. Memory Repository And CRUD APIs

- [x] 3.1 Implement backend memory repository functions for create, read, list, update, search metadata, archive, delete, and event append.
- [x] 3.2 Implement tombstone creation for deletes while removing deleted records from default injectable views.
- [x] 3.3 Add memory list/read/create/update/delete API endpoints with bounded payloads and structured errors.
- [x] 3.4 Add filters for scope, type, status, tag, project root/root ID, session/thread ID, and query.
- [x] 3.5 Record redacted memory events for create, update, archive, delete, and read-sensitive lifecycle actions.
- [x] 3.6 Ensure memory APIs write only to Kira-owned SQLite storage and never mutate project roots.
- [x] 3.7 Add API tests for CRUD, filters, tombstones, event recording, not-found errors, project non-mutation, and redaction.

## 4. Retrieval, Ranking, And Explanations

- [x] 4.1 Implement deterministic lexical memory search with query overlap, scope match, type match, tag match, confidence, recency, and prior-usefulness scoring.
- [x] 4.2 Implement scope resolution for run/session/project context so unrelated project/user memories are excluded by default.
- [x] 4.3 Implement status filtering so archived, deleted, stale, expired, and out-of-scope memories are not injected by default.
- [x] 4.4 Implement top-k limits, memory budget limits, and omitted-count metadata.
- [x] 4.5 Implement dedupe by normalized text and merge relationships, with duplicate IDs surfaced in explanations.
- [x] 4.6 Implement score reason objects with matched fields and per-factor contribution values.
- [x] 4.7 Persist retrieval traces with redacted query metadata and selected/omitted memory IDs.
- [x] 4.8 Add tests for deterministic ranking, filters, status exclusions, top-k, budget omissions, dedupe, score reasons, and retrieval trace redaction.

## 5. Context Injection And Citations

- [x] 5.1 Convert selected memory retrieval results into `ContextItem(kind="memory")` records with trust label, budget cost, retrieval metadata, and memory citations.
- [x] 5.2 Extend context budget packing to include memory items in deterministic priority order with truncation and omission records.
- [x] 5.3 Add memory citation records whenever memory ContextItems are included in a run.
- [x] 5.4 Extend run context traces to show memory IDs, citation IDs, scopes, types, scores, score reasons, trust labels, budget costs, truncations, and omissions.
- [x] 5.5 Keep memory citations distinct from project citations when both are present in one run.
- [x] 5.6 Update provider request assembly so memory is injected only through ContextItems and never through raw prompt concatenation outside the context builder.
- [x] 5.7 Add tests for memory ContextItem conversion, mixed project/memory citations, budget omissions, provider injection path, and no secret leakage in traces.

## 6. Run API Integration And Replay

- [x] 6.1 Extend run creation payloads with memory retrieval controls, scope filters, type filters, top-k, and memory budget options.
- [x] 6.2 Integrate memory retrieval before provider input assembly for direct provider runs and skill graph runs.
- [x] 6.3 Add run response metadata for memory retrieval counts, omitted counts, and redacted retrieval status.
- [x] 6.4 Extend run state projection with redacted memory retrieval and citation summaries.
- [x] 6.5 Extend replay/debug export with memory usage summaries without rerunning retrieval or extraction.
- [x] 6.6 Ensure replay requests do not create new memory records, events, candidates, citations, retrieval traces, provider calls, tools, or lifecycle actions.
- [x] 6.7 Add tests for run memory controls, direct provider memory injection, skill graph memory injection, fixture fallback, state/replay summaries, and replay read-only behavior.

## 7. Extraction Dry-Run And Candidate Review

- [x] 7.1 Implement extraction input builder from bounded run summaries, user feedback, selected skill metadata, workflow outcome, tool summaries, and redacted provider metadata.
- [x] 7.2 Implement deterministic fixture/mock extractor that produces stable MemoryCandidate fixtures without requiring a real API key.
- [x] 7.3 Implement optional real-provider extraction path that is skipped unless valid provider config and explicit extraction mode are present.
- [x] 7.4 Apply secret guard and dedupe before candidate persistence or approval.
- [x] 7.5 Persist extraction candidates with source, reason, confidence, risk, guard status, duplicate IDs, suggested scope, and suggested type.
- [x] 7.6 Add candidate APIs for dry-run extraction, list, read, approve, reject, edit, and defer.
- [x] 7.7 Ensure dry-run extraction never creates active memory records without explicit approval/write action.
- [x] 7.8 Add tests for fixture extraction, no-key behavior, skipped real smoke test, secret candidate blocking, duplicate candidate marking, approval writes, rejection, edit, and no automatic writes.

## 8. Lifecycle Actions And HITL Approval

- [x] 8.1 Implement archive action that stops default injection while preserving memory record and events.
- [x] 8.2 Implement delete action that creates tombstones and removes the memory from injectable records.
- [x] 8.3 Implement merge action that preserves prior IDs, source metadata, citations, and events while preventing duplicate injection.
- [x] 8.4 Implement refresh action that updates confidence, source summaries, tags, and last-reviewed metadata with redacted evidence.
- [x] 8.5 Implement stale action that marks expired or conflicting memory non-injectable by default.
- [x] 8.6 Implement promote action from `session`/`projectLocal` to broader scope with approval requirement when policy requires it.
- [x] 8.7 Reuse Stage 05 HITL interrupt/resume semantics for memory write or promotion approval prompts.
- [x] 8.8 Add tests for archive, delete, merge, refresh, stale, promote, approval required, approved promotion, rejected promotion, and unsafe lifecycle rejection.

## 9. Frontend Memory Inspector

- [x] 9.1 Add memory API client functions for list, search, read, create, update, delete, lifecycle actions, extraction dry-run, and candidate decisions.
- [x] 9.2 Add frontend memory types for records, sources, citations, explanations, score reasons, candidates, guard results, and lifecycle responses.
- [x] 9.3 Add memory inspector panel to the existing workbench inspector without changing the Stage 09 visual direction.
- [x] 9.4 Implement memory list with scope/type/status/tag/query filters, empty states, loading states, and error states.
- [x] 9.5 Implement memory search/explain view showing score reasons, matched fields, citations, dedupe omissions, and budget omissions.
- [x] 9.6 Implement manual add/edit form with validation feedback for scope, type, confidence, tags, text, and source summary.
- [x] 9.7 Implement lifecycle controls for archive, delete, merge, refresh, stale, and promote with backend result handling.
- [x] 9.8 Implement extraction candidate review with approve, reject, edit, defer, confidence, risk, guard status, and duplicate indicators.
- [x] 9.9 Extend run context inspector to show memory ContextItems and memory citations alongside project citations.
- [x] 9.10 Add frontend tests for memory list/filter/search, explanation rendering, add/edit validation, lifecycle actions, candidate review, context inspector memory citations, and no-secret DOM rendering.

## 10. Fixtures, Regression, And Documentation

- [x] 10.1 Add memory fixture records covering all scopes, types, statuses, confidence levels, tags, duplicate groups, stale records, expired records, and source metadata.
- [x] 10.2 Add secret fixtures for API keys, bearer tokens, cookies, private keys, `.env` values, provider configs, provider errors, and high-risk personal/customer data.
- [x] 10.3 Add extraction fixture runs covering user preference, project decision, workflow lesson, feedback, duplicate candidate, and blocked secret candidate.
- [x] 10.4 Verify Stage 01 local web loop regression tests for health, run creation, event streaming, and frontend boot.
- [x] 10.5 Verify Stage 02 tool protocol regression tests for read-only project policy and controlled Python execution.
- [x] 10.6 Verify Stage 03 skill graph regression tests for workflow discovery, graph execution, and fixture runs.
- [x] 10.7 Verify Stage 04 durability/replay regression tests for events, projections, checkpoints, locks, and replay.
- [x] 10.8 Verify Stage 05 HITL regression tests for interrupt/resume and memory approval reuse.
- [x] 10.9 Verify Stage 06 skill/project context regression tests for skill packages, project citations, ContextItems, and no project mutation.
- [x] 10.10 Document memory record shape, scopes, types, statuses, lifecycle actions, retrieval explanations, extraction dry-run, and secret guard in project docs.
- [x] 10.11 Run backend unit and integration tests for `server/`.
- [x] 10.12 Run shared schema/type validation for `src/`.
- [x] 10.13 Run frontend typecheck and tests for `web/`.
- [x] 10.14 Run `openspec validate "stage-07-memory-system" --strict`.
- [x] 10.15 Run `openspec status --change "stage-07-memory-system"` and confirm the change is ready for apply.
