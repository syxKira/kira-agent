## Why

Stage 08a made conversation history durable and Stage 08b added explicit compaction and replacement context, but conversations are still effectively linear. Stage 08c completes the Stage 08 transcript model by adding safe fork and rollback primitives so users can branch from an earlier message, abandon later turns without deleting them, and keep provider context tied to the selected active parent chain.

## What Changes

- Add conversation fork support from a selected message or turn into a new conversation with provenance back to the source conversation/message/turn.
- Add rollback support that moves a conversation's `active_head_message_id` back to a selected active-chain message without deleting later transcript records.
- Add branch provenance records and active-head transition records for fork and rollback operations.
- Mark fork sources, rolled-back messages, and inactive branch messages with frontend-safe branch status metadata.
- Ensure future runs after rollback parent new user messages from the rollback head and omit abandoned later messages from provider context.
- Ensure conversation context traces explain included active-chain items and omitted inactive branch items.
- Add structured conflict handling when a resume is attempted for an interrupted `thread_id` whose turn is no longer on the selected conversation active chain.
- Expose fork/rollback APIs and minimal frontend controls/inspector metadata without Stage 10 visual redesign.
- Preserve Stage 08 guarantees: hidden thinking is never visible transcript or provider history; compaction/replacement artifacts remain bounded; transcript remains separate from Stage 07 memory.

Out of scope for this focused Stage 08c slice:

- Stage 09 audit hardening, deletion policy, retained replacement blob inspection policy, doctor, and full trace export.
- Stage 10 polished branch graph UI, task rail redesign, and product-grade conversation browsing.
- Destructive transcript deletion, multi-user collaboration, cloud sync, OS sandboxing, project mutation tools, or general shell tools.

## Capabilities

### New Capabilities

- `conversation-branching`: Defines fork, rollback, active-head transition, branch provenance, inactive branch omission, and resume conflict behavior.

### Modified Capabilities

- `conversation-transcript-core`: Store fork/rollback marker parts and branch status metadata while keeping source transcript rows inspectable.
- `conversation-history-context`: Omit inactive branch messages from provider input and trace active-chain versus inactive-branch decisions.
- `durable-run-storage`: Add local branch/active-head transition storage and branch metadata needed for fork/rollback.
- `local-run-api`: Add fork and rollback endpoints plus structured resume conflict responses when active head moved past an interrupted turn.
- `local-web-workbench`: Add minimal fork/rollback controls and branch/active-head inspector metadata.
- `run-state-replay`: Include frontend-safe fork/rollback and active-head metadata in state/replay without mutating transcript or branch state.
- `hitl-interrupt-resume`: Preserve thread-scoped resume while detecting conflicts when the conversation branch no longer contains the interrupted turn.

## Impact

- Backend `server/`: transcript branching service, SQLite migrations, conversation fork/rollback APIs, context builder active-chain checks, resume conflict checks, state/replay projection updates, tests.
- Frontend `web/`: API client functions, minimal fork/rollback controls, branch status and conflict rendering, tests.
- Shared `src/`: schemas for fork/rollback requests/responses, branch records, active-head transitions, resume conflict metadata, and Stage 08c fixtures.
- Existing behavior: linear conversation runs continue unchanged; fork/rollback are explicit user actions; existing transcript, compaction, replacement, memory, project, and graph records remain readable.
