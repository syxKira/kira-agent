## 1. Shared Contracts

- [x] 1.1 Add shared JSON schemas for fork request/response, rollback request/response, branch records, active-head transitions, inactive branch trace metadata, and resume conflict metadata.
- [x] 1.2 Extend conversation transcript schemas with branch status, fork marker metadata, rollback marker metadata, and active-chain/inactive-branch references.
- [x] 1.3 Extend run context, run state, and replay schemas with active head at run creation, fork source metadata, rollback transition metadata, and inactive branch omission records.
- [x] 1.4 Add Stage 08c schema fixtures for fork, rollback, run-after-rollback, inactive branch omission, and resume conflict.
- [x] 1.5 Export frontend TypeScript types for fork/rollback APIs, branch records, active-head transitions, transcript branch metadata, and resume conflict responses.

## 2. Storage And Repository

- [x] 2.1 Add idempotent SQLite migrations for conversation branch records and active-head transition records.
- [x] 2.2 Add any needed conversation/transcript columns or indexes for fork source, branch status, active-chain lookup, and transition lookup.
- [x] 2.3 Implement repository methods for creating and reading fork branch records.
- [x] 2.4 Implement repository methods for creating and reading rollback transition records.
- [x] 2.5 Implement active-chain validation helpers for determining whether a message or turn belongs to a conversation's current active parent chain.
- [x] 2.6 Implement inactive branch derivation or persisted branch-status update helpers for transcript reads and context traces.
- [x] 2.7 Add migration tests proving Stage 04-08b run, transcript, compaction, replacement, project, and memory records remain readable after branch migrations.
- [x] 2.8 Add repository tests for fork provenance, rollback transition storage, active-chain validation, invalid source rejection, inactive branch derivation, redacted reason metadata, and idempotent migrations.

## 3. Fork And Rollback Services

- [x] 3.1 Implement transcript service method to fork a conversation from a valid active-chain message or turn.
- [x] 3.2 Ensure fork creates a new conversation with source conversation/message/turn metadata and active head at the fork point.
- [x] 3.3 Ensure fork rejects unknown, archived, cross-conversation, or inactive source messages without side effects.
- [x] 3.4 Implement transcript service method to roll back a conversation active head to a valid active-chain message or turn.
- [x] 3.5 Ensure rollback records previous active head, new active head, reason metadata, and affected inactive branch summary without deleting transcript rows.
- [x] 3.6 Ensure new runs after rollback parent user messages from the rollback head.
- [x] 3.7 Ensure fork/rollback operations create bounded transcript marker metadata without appearing as visible assistant answer text.
- [x] 3.8 Ensure fork/rollback operations do not create memory records, provider calls, tool calls, compaction summaries, or replacement records unless explicitly required by later run execution.
- [x] 3.9 Add backend service tests for fork success, fork isolation, invalid fork rejection, rollback success, rollback non-deletion, run-after-rollback parentage, marker metadata, and no automatic memory writes.

## 4. Context Builder And Resume Conflicts

- [x] 4.1 Extend conversation context building to omit messages outside the current active parent chain after rollback.
- [x] 4.2 Ensure forked conversation context includes inherited history only up to the fork point plus fork-local future turns.
- [x] 4.3 Ensure source conversation future messages after a fork are never injected into the fork.
- [x] 4.4 Ensure compaction summaries that cover inactive branch-only messages are omitted or marked stale for the current active branch.
- [x] 4.5 Extend transcript context traces with active head, fork source boundary, rollback transition ID, included active-chain items, and omitted inactive branch items.
- [x] 4.6 Add resume conflict detection when an interrupted `thread_id` belongs to a turn outside the current active chain.
- [x] 4.7 Ensure same-chain HITL resume continues existing `thread_id` and turn without creating a new user message.
- [x] 4.8 Add tests for inactive branch omission, fork source future omission, summary invalidation after rollback, branch trace metadata, resume conflict response, and same-chain resume compatibility.

## 5. API, State, And Replay

- [x] 5.1 Add `POST /api/conversations/{conversation_id}/fork` with source message/turn input and frontend-safe response metadata.
- [x] 5.2 Add `POST /api/conversations/{conversation_id}/rollback` with target message/turn input and frontend-safe response metadata.
- [x] 5.3 Add structured validation/not-found responses for unknown, archived, inactive, or cross-conversation fork/rollback targets.
- [x] 5.4 Extend `POST /api/runs` behavior so branch-aware active head is captured in run state and context traces.
- [x] 5.5 Extend `POST /api/runs/{thread_id}/resume` responses with structured inactive-branch conflict metadata.
- [x] 5.6 Extend conversation transcript and context endpoints with branch status, active-head, fork source, rollback transition, and inactive branch omission metadata.
- [x] 5.7 Extend run state projection with branch metadata observed at run creation.
- [x] 5.8 Extend replay/debug export with saved branch metadata while keeping replay read-only and avoiding active-head mutation.
- [x] 5.9 Add API tests for fork endpoint, rollback endpoint, validation failures, run-after-rollback, context metadata, transcript metadata, resume conflict, state linkage, replay read-only behavior, and redaction.

## 6. Frontend Workbench

- [x] 6.1 Add frontend API client functions for fork conversation and rollback conversation.
- [x] 6.2 Add minimal transcript message selection state needed for fork/rollback controls.
- [x] 6.3 Add basic fork control that creates/selects the forked conversation and refreshes transcript/context.
- [x] 6.4 Add basic rollback control that refreshes transcript/context and shows the new active head.
- [x] 6.5 Render branch status, fork source, rollback transition, active head, and inactive branch metadata in existing conversation/transcript/context surfaces.
- [x] 6.6 Render structured resume conflict state without raw hidden thinking or provider secrets.
- [x] 6.7 Add frontend tests for fork action, rollback action, conversation switching after fork, inactive branch metadata, context inspector branch omissions, resume conflict display, and no-secret/no-hidden-thinking rendering.

## 7. Documentation And Verification

- [x] 7.1 Document Stage 08c fork/rollback versus transcript, compaction, memory, and `thread_id` responsibilities in README and server/web/src docs.
- [x] 7.2 Document fork/rollback API payloads, response metadata, inactive branch context behavior, and resume conflict behavior.
- [x] 7.3 Run backend unit and integration tests for `server/`.
- [x] 7.4 Run shared schema validation for `src/`.
- [x] 7.5 Run frontend typecheck and tests for `web/`.
- [x] 7.6 Run `openspec validate "stage-08c-fork-rollback" --strict`.
- [x] 7.7 Run `openspec status --change "stage-08c-fork-rollback"` and confirm the change is ready for apply.
