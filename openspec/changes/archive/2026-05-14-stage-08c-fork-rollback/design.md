## Context

Stage 08a introduced the local conversation transcript model: `conversation_id`, `turn_id`, parent-linked messages, active head, and conversation history ContextItems. Stage 08b added explicit compaction summaries and replacement stubs. The remaining Stage 08 gap is branch control: users cannot yet fork from an earlier transcript point or roll back the active head without deleting transcript rows.

Fork/rollback must preserve the distinction between `conversation_id` continuity and `thread_id` execution. It must also preserve Stage 08's safety boundaries: provider input is built only from the active parent chain, hidden thinking is excluded, compaction/replacement artifacts stay bounded, and transcript is not memory.

## Goals / Non-Goals

**Goals:**

- Add explicit fork and rollback APIs for conversations.
- Preserve branch provenance with source conversation, source message, source turn, source active head, and resulting active head metadata.
- Keep rollback non-destructive: later messages remain inspectable but inactive for future context.
- Ensure new runs after rollback parent from the rollback head.
- Ensure forked conversations inherit context only up to the fork point and are isolated from future source-conversation messages.
- Record fork/rollback transcript marker parts and active-head transition records.
- Expose inactive branch omissions and active-head decisions in context traces, state, replay, and minimal frontend UI.
- Detect resume conflicts when a pending interrupted run is no longer on the active chain after rollback/fork decisions.

**Non-Goals:**

- No Stage 09 audit hardening, destructive deletion policy, doctor, full trace export, or retained replacement blob inspection policy.
- No Stage 10 polished branch graph UI or task rail redesign.
- No destructive transcript deletion, cloud sync, multi-user branching, OS sandboxing, project mutation tools, or general shell.
- No automatic memory creation from fork or rollback events.

## Decisions

### Rollback Moves Active Head, Not Rows

Rollback will update `conversations.active_head_message_id` to a selected message on the current active chain and store a rollback transition record. Transcript messages after the rollback point remain in storage and are marked or derived as inactive for context.

Alternative considered: delete messages after rollback. Rejected because deletion needs Stage 09 audit/policy, breaks replay/debug, and removes provenance the user may need later.

### Fork Creates A New Conversation With Provenance

Fork will create a new conversation whose active head points at the selected source message. The source transcript rows are referenced by parent/provenance metadata rather than physically copied unless implementation needs lightweight marker rows for UI. Future turns in the fork use the new conversation ID.

Alternative considered: keep fork as another branch inside the same conversation only. Rejected for Stage 08c because separate `conversation_id` isolation is easier to reason about and matches existing workbench selection behavior.

### Active Chain Is The Only Provider History

The context builder will continue walking from `active_head_message_id` through parent links. Messages outside that chain are omitted from provider input and recorded as inactive branch omissions when relevant to inspection.

Alternative considered: include inactive branch messages with lower priority. Rejected because rollback semantics must mean "do not use abandoned future context" unless the user explicitly forks/selects it.

### Resume Conflicts Are Structured

Resume remains thread-scoped. If a pending interrupted `thread_id` belongs to a turn no longer on the conversation active chain, the backend returns a structured conflict instead of silently resuming into a branch the user rolled back past.

Alternative considered: always allow resume regardless of active head. Rejected because it can append events to a turn the user has explicitly abandoned.

### Frontend Controls Stay Functional

Stage 08c adds minimal fork/rollback controls and metadata in existing workbench surfaces. Stage 10 owns polished branch visualization.

Alternative considered: wait for Stage 10 UI. Rejected because fork/rollback must be usable and testable before Stage 09 safety and Stage 10 polish.

## Risks / Trade-offs

- [Risk] Shared source rows across forked conversations can complicate transcript reads. -> Mitigation: expose provenance explicitly and keep provider context based on each conversation's active head.
- [Risk] Rollback may surprise users if later messages disappear from context. -> Mitigation: make rollback explicit, non-destructive, and visible in transcript/context inspector.
- [Risk] Resume conflict handling can interrupt existing HITL workflows. -> Mitigation: conflict only when the interrupted turn is outside active chain; same-chain resumes continue unchanged.
- [Risk] Compaction summaries may cover messages that become inactive after rollback. -> Mitigation: context builder omits summaries not valid for the active chain and traces inactive/stale reasons.
- [Risk] Branch status can become inconsistent after repeated rollback/fork. -> Mitigation: use transition records as source of truth and add tests for chained operations.

## Migration Plan

1. Add shared schemas for branch records, active-head transitions, fork/rollback requests/responses, inactive branch trace metadata, and resume conflict metadata.
2. Add idempotent SQLite migrations for conversation branch/active-head transition records and needed conversation metadata columns.
3. Implement backend fork and rollback service methods with active-chain validation.
4. Integrate active-chain omission and branch trace metadata into context building.
5. Add resume conflict checks before accepting HITL resume.
6. Expose fork/rollback APIs and minimal frontend controls.
7. Extend state/replay with saved branch metadata without mutating branch state.
8. Add backend/frontend/schema/OpenSpec validation coverage.

Rollback strategy: migrations are additive. If branch features are disabled, existing linear conversations continue using the Stage 08a/08b active-head path.

## Open Questions

- Should a forked conversation initially display referenced source messages as read-only inherited messages or as a compact provenance banner plus active transcript?
- Should rollback require selecting only assistant messages, or any active-chain user/assistant message?
- Should the UI default to creating a fork before rollback for safer experimentation, or keep both explicit actions side by side?
