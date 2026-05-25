## Why

Stage 08a made conversations durable and usable for ordinary follow-up prompts, but long conversations still rely on a recent raw-history window and bounded omission. Without explicit compaction and first-class tool-output replacement, useful older context can disappear silently, large tool outputs can overwhelm prompt budgets, and users cannot inspect why a transcript changed shape.

This Stage 08b slice adds the next transcript layer: explicit compaction summaries, stale/refresh rules, replacement stubs for large or sensitive tool output, and context traces that explain summary/replacement decisions.

## What Changes

- Add explicit conversation compaction records that summarize older active-chain transcript spans without rewriting or deleting source messages.
- Add deterministic fixture summarization by default, with optional real-provider summarization only when a valid provider is configured.
- Add stale detection for compaction summaries when covered transcript messages or replacement records change.
- Add manual compaction API and overflow-triggered compaction path for runs that exceed transcript context limits.
- Add `conversation_summary` and `compaction_summary` ContextItem support alongside recent `conversation_history` and `tool_summary`.
- Add tool-output replacement records for oversized or sensitive tool outputs, including bounded model-visible stubs, hashes, omitted counts, retention metadata, and redacted references.
- Update conversation transcript/context APIs, state projection, replay/debug export, and the workbench inspector to expose frontend-safe summary and replacement metadata.
- Preserve Stage 08a guarantees: `conversation_id` remains the continuity cursor, `thread_id` remains the run/resume cursor, hidden thinking is never visible transcript or provider history, and transcript remains separate from Stage 07 memory.

Out of scope for this focused Stage 08b slice:

- Stage 08c fork and rollback APIs, inactive branch UI, active-head conflict handling for resumed abandoned threads, and branch graph controls.
- Stage 09 audit/doctor/trace export hardening, permission policy for resolving retained replacement blobs, and transcript deletion safety polish.
- Stage 10 product-grade conversation UI redesign.
- Cloud transcript sync, multi-user collaboration, vector databases, project mutation tools, general shell tools, or automatic transcript-to-memory writes.

## Capabilities

### New Capabilities

- `conversation-compaction`: Defines explicit compaction summary records, manual and overflow-triggered compaction, summary stale/refresh behavior, summarizer selection, and summary ContextItems.
- `tool-output-replacement`: Defines replacement records for large or sensitive tool output, bounded provider stubs, redacted local retention metadata, output hashes, and replacement trace behavior.

### Modified Capabilities

- `conversation-history-context`: Prefer non-stale compaction summaries for older active-chain spans, append recent raw tail, include replacement stubs/tool summaries, and trace omitted or stale transcript context.
- `conversation-transcript-core`: Store compaction and replacement transcript artifacts without changing visible answer text or deleting source messages.
- `context-item-budgeting`: Add `conversation_summary` and `compaction_summary` ContextItem kinds, budget priorities, and omission metadata for summaries/replacements.
- `durable-run-storage`: Add SQLite tables or columns for compaction summaries and tool-output replacement records while preserving Stage 04-08a data.
- `local-run-api`: Add compact endpoint behavior and expose summary/replacement metadata through conversation transcript/context and run context responses.
- `local-web-workbench`: Show compacted summary and replacement-stub metadata in the existing inspector/conversation surfaces without a Stage 10 redesign.
- `run-state-replay`: Include frontend-safe compaction/replacement summaries in state and replay without regenerating summaries or resolving raw replacement content.

## Impact

- Backend `server/`: storage migrations, transcript compaction service, summarizer adapter, tool-output replacement repository, run/context builder integration, conversation compact API, replay/state projection updates, tests.
- Frontend `web/`: API client types/functions, conversation/context inspector rows for summaries and replacement stubs, minimal compact control, tests.
- Shared `src/`: schema updates for compaction summaries, replacement records, ContextItem kinds, run context traces, and example fixtures.
- Existing behavior: Stage 08a conversations continue to work; existing transcript rows remain readable; no real API key is required by default because fixture summarization is deterministic.
