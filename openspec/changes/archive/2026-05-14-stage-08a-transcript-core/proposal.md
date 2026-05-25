## Why

Kira can run real providers, skills, project retrieval, and memory, but each normal `Run` is still effectively a one-shot prompt. A follow-up such as "what did I just say?" cannot use the prior turn unless the user manually repeats it, because `thread_id` is a run/resume cursor and Stage 07 memory deliberately is not transcript history.

This change implements the focused Stage 08a core needed for real multi-turn local conversations: persistent conversation/turn/transcript records, run linkage, visible assistant text persistence, and bounded conversation history ContextItems.

## What Changes

- Add `conversation_id` as the local multi-turn continuity cursor, separate from `thread_id`.
- Add `turn_id`, transcript messages, transcript parts, parent message links, active conversation head, and run-to-turn linkage in Kira-owned SQLite storage.
- Extend `POST /api/runs` to accept optional `conversation_id`, create one when omitted, persist the user message before execution, and return `conversation_id` plus `turn_id`.
- Persist visible assistant `text_delta` chunks into assistant transcript messages and mark transcript/run status on `done`, `error`, cancel, and resume.
- Persist bounded non-answer transcript markers for tool summaries, interrupt/resume markers, and errors.
- Add conversation APIs for create/list/read/update, transcript read, and context inspection.
- Add conversation history ContextItems built from the active parent chain and recent visible turns.
- Extend context traces to show included/truncated/omitted transcript context.
- Update the frontend workbench to keep a selected conversation across follow-up runs and render prior visible transcript from backend state.
- Keep hidden thinking out of visible transcript and out of conversation history ContextItems.

Out of scope for this focused Stage 08a slice:

- Explicit compaction summaries, summary refresh/stale rules, and overflow-triggered summarization.
- Tool-output replacement blobs/stubs beyond bounded summaries for transcript core.
- Fork and rollback APIs, inactive branch omission, and resume conflict handling for branch changes.
- Stage 09 safety/observability audit, doctor, trace export, and permission hardening.
- Stage 10 product-grade visual redesign.

## Capabilities

### New Capabilities

- `conversation-transcript-core`: Defines conversations, turns, transcript messages/parts, parent links, active head, run linkage, transcript persistence rules, and conversation APIs.
- `conversation-history-context`: Defines active-parent-chain transcript context selection, conversation history ContextItems, hidden-thinking exclusion, budget omission trace, and conversation isolation.

### Modified Capabilities

- `durable-run-storage`: Add SQLite tables for conversations, turns, transcript messages/parts, run links, and transcript context traces.
- `context-item-budgeting`: Add conversation history/tool-summary ContextItem kinds and budget trace behavior.
- `local-run-api`: Add `conversation_id` input, `conversation_id`/`turn_id` response metadata, conversation APIs, and transcript context controls.
- `run-state-replay`: Include frontend-safe conversation/turn/transcript linkage in state and replay without rebuilding transcript context.
- `local-web-workbench`: Keep selected conversation across runs, render prior transcript messages, and expose basic conversation list/create behavior.

## Impact

- Backend `server/`: storage migrations, transcript service/repository, run creation/event streaming integration, conversation API routes, context builder integration, tests.
- Frontend `web/`: API client types/functions, selected conversation state, transcript loading/rendering, run creation payload/response handling, context inspector updates, tests.
- Shared `src/`: transcript/conversation JSON schemas and ContextItem schema updates.
- Existing Stage 01-07 behavior must remain compatible: fixture runs still work, provider fallback remains unchanged, HITL resume still uses `thread_id`, memory remains separate from transcript, and project files remain read-only.
