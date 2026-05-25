## 1. Shared Contracts

- [x] 1.1 Add shared JSON schemas for compaction summaries, tool-output replacement records, compact API request/response, and Stage 08b transcript context trace metadata.
- [x] 1.2 Extend `context-item.schema.json` with `conversation_summary` and `compaction_summary` kinds plus summary/replacement reference metadata.
- [x] 1.3 Extend run context, run state, run replay, and conversation transcript schemas to include summary IDs, replacement IDs, stale status, source ranges, omitted counts, retention policy, and budget decisions.
- [x] 1.4 Add Stage 08b schema fixtures for manual compaction, overflow compaction, stale summary omission, and replacement stub context.
- [x] 1.5 Export frontend TypeScript types for compaction summaries, compact responses, replacement records, summary ContextItems, and replacement trace rows.

## 2. Storage And Repository

- [x] 2.1 Add idempotent SQLite migrations for `conversation_compaction_summaries` with source ranges, source hash, tail boundary, token estimates, summarizer metadata, status, stale reason, previous summary ID, and timestamps.
- [x] 2.2 Add idempotent SQLite migrations for `tool_output_replacements` with source conversation/turn/thread/message/part IDs, tool name, output hash, summary, omitted count, reason, retention policy, status, redacted reference metadata, and timestamps.
- [x] 2.3 Add storage indexes for looking up active conversation summaries, stale summaries, summaries by source range, replacements by source part, and replacements by conversation.
- [x] 2.4 Implement repository methods for creating, reading, listing, refreshing, and marking stale compaction summaries.
- [x] 2.5 Implement repository methods for creating, reading, listing, and invalidating tool-output replacement records.
- [x] 2.6 Add migration tests proving Stage 04 run records, Stage 06 project index records, Stage 07 memory records, and Stage 08a transcript records remain readable after Stage 08b migrations.
- [x] 2.7 Add repository tests for source hash calculation, stale marking, previous-summary linkage, replacement redaction, hash metadata, retention metadata, and idempotent migration behavior.

## 3. Summarizer And Replacement Services

- [x] 3.1 Implement a deterministic fixture transcript summarizer that preserves goals, constraints, decisions, unresolved questions, selected skills, project root, bounded tool outcomes, and source references.
- [x] 3.2 Implement optional real-provider summarization through the existing OpenAI-compatible provider layer without exposing raw API keys or hidden thinking.
- [x] 3.3 Implement summarizer selection rules: explicit request override when allowed, configured real provider when valid, fixture fallback when no valid key or tests request deterministic behavior.
- [x] 3.4 Implement summary guard/redaction for secrets, raw provider config, raw provider errors, hidden thinking, and unbounded tool output.
- [x] 3.5 Implement replacement creation for oversized tool output with bounded summary, output hash, omitted character count, reason, retention policy, and source IDs.
- [x] 3.6 Implement replacement creation for secret-guarded tool output so provider input, transcript, traces, replay, state, and frontend responses receive only redacted stubs.
- [x] 3.7 Add unit tests for fixture summary determinism, real-provider summarizer mocking, provider fallback, summary redaction, replacement thresholding, secret replacement, and replacement hash stability.

## 4. Transcript Compaction Integration

- [x] 4.1 Add transcript service methods for manual compaction over the selected conversation active parent chain.
- [x] 4.2 Store compaction summaries as transcript/context artifacts without changing restored visible assistant answer text.
- [x] 4.3 Mark summaries stale when covered messages, covered parts, or referenced replacement records change status, text, hash, or retention metadata.
- [x] 4.4 Refresh stale summaries by creating a new summary linked to `previous_summary_id` while preserving the stale summary for inspection.
- [x] 4.5 Add overflow detection based on configurable transcript thresholds for message count, estimated tokens/characters, and context budget pressure.
- [x] 4.6 Add overflow-triggered compaction before final provider input assembly when enabled and thresholds are exceeded.
- [x] 4.7 Ensure compaction failure falls back to Stage 08a bounded recent-history behavior and records structured redacted errors in the context trace.
- [x] 4.8 Add backend tests for manual compaction, overflow compaction, stale detection, refresh linkage, fallback behavior, no source-message deletion, no hidden-thinking inclusion, and no automatic memory writes.

## 5. Context Builder And Provider Input

- [x] 5.1 Extend active-chain context building to select the latest non-stale compaction summary for older spans and recent raw `conversation_history` after `tail_start_message_id`.
- [x] 5.2 Emit `conversation_summary` and `compaction_summary` ContextItems with source ranges, summary IDs, stale status, trust labels, citations/references, and budget costs.
- [x] 5.3 Prevent duplicate injection of raw messages already covered by included non-stale summaries.
- [x] 5.4 Include bounded replacement stubs or `tool_summary` ContextItems for relevant prior replacements without injecting raw replaced output.
- [x] 5.5 Extend transcript context traces with included/truncated/omitted/stale/refreshed decisions for summaries, raw messages, tool summaries, and replacement stubs.
- [x] 5.6 Preserve conversation isolation and memory separation when summaries and replacements are present.
- [x] 5.7 Add tests for summary-plus-tail ordering, stale summary omission, duplicate raw-message prevention, replacement stub inclusion/omission, mixed skill/project/memory/summary context, and hidden-thinking exclusion.

## 6. API, State, And Replay

- [x] 6.1 Add `POST /api/conversations/{conversation_id}/compact` with optional summarizer/provider mode, threshold, tail, and refresh controls.
- [x] 6.2 Return frontend-safe compaction response metadata including summary ID, status, source range, tail boundary, stale status, summarizer metadata, token estimates, and omissions.
- [x] 6.3 Reject compact requests for unknown or archived conversations without creating providers calls, summaries, transcript parts, replacements, tools, or memory records.
- [x] 6.4 Extend `GET /api/conversations/{conversation_id}/transcript` to expose summary and replacement metadata safely.
- [x] 6.5 Extend `GET /api/conversations/{conversation_id}/context` and `GET /api/runs/{thread_id}/context` to expose summary/replacement ContextItems and trace decisions.
- [x] 6.6 Extend run state projection with compaction summary and replacement references used by the run.
- [x] 6.7 Extend replay/debug export with saved summary/replacement metadata while keeping replay read-only and avoiding provider/tool/blob resolution.
- [x] 6.8 Add API tests for compact success, compact fallback, not-found/archive rejection, context metadata, transcript metadata, state linkage, replay read-only behavior, and secret redaction.

## 7. Frontend Workbench

- [x] 7.1 Add frontend API client functions for compact conversation and updated transcript/context metadata.
- [x] 7.2 Add minimal compact control in the existing conversation side panel or inspector without Stage 10 visual redesign.
- [x] 7.3 Show compacting, success, and bounded error states without exposing raw provider errors or secrets.
- [x] 7.4 Render compaction summaries as metadata/context rows rather than normal assistant answer text.
- [x] 7.5 Render replacement stubs with replacement ID, reason, omitted count, source part ID, retention policy, and bounded summary while hiding raw replaced output.
- [x] 7.6 Update context inspector to display `conversation_summary`, `compaction_summary`, stale summary omissions, and replacement budget decisions.
- [x] 7.7 Add frontend tests for compact action, transcript restore with summary metadata, context inspector summary rows, replacement stub rows, stale/omitted states, and no-secret/no-hidden-thinking rendering.

## 8. Documentation And Verification

- [x] 8.1 Document Stage 08b compaction versus transcript versus memory responsibilities in README and server/web/src docs.
- [x] 8.2 Document compact API payload/response fields, summarizer fallback behavior, replacement retention policy, and replay read-only semantics.
- [x] 8.3 Run backend unit and integration tests for `server/`.
- [x] 8.4 Run shared schema validation for `src/`.
- [x] 8.5 Run frontend typecheck and tests for `web/`.
- [x] 8.6 Run `openspec validate "stage-08b-context-compaction" --strict`.
- [x] 8.7 Run `openspec status --change "stage-08b-context-compaction"` and confirm the change is ready for apply.
