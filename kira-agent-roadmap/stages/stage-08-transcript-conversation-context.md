# Stage 08: Transcript + Conversation Context

## Goal

Turn Kira from single-run prompt execution into a real multi-turn web agent: persistent conversations, ordered transcripts, parent-linked message history, conversation-aware context building, explicit context compaction, tool-output replacement, fork/rollback, run-to-conversation linking, and frontend conversation continuity. A user can ask a follow-up question and Kira can see the relevant prior turns without turning short-term dialogue into long-term memory.

## Why This Stage

Stage 04 made `thread_id` reliable for a single graph/run lineage. Stage 07 made durable memory available for selected facts, decisions, preferences, and lessons. Neither one is the chat transcript.

For a Web Agent, the missing object is `conversation_id`: a stable local chat/session container that owns user/assistant messages and links each assistant response to the `thread_id` that produced it. The next run should receive bounded recent transcript plus explicit compaction summaries, recent active-tail messages, and optional tool summaries as ContextItems. Memory extraction can read the transcript after a run, but memory must not replace transcript.

Mature local agents do not treat chat history as a flat append-only string. Claude Code persists session transcripts with parent links, resume metadata, summaries, and context-collapse records; Codex models threads, turns, and structured items; OpenCode models session messages as message/part records with compaction, reasoning, tool, retry, and output-pruning states. Kira should adopt the same core ideas while keeping the implementation local, Web-first, and non-code-specific.

## Scope

- `conversation_id` as the stable multi-turn chat/session ID.
- A `turn_id` for each user request and assistant response pair.
- Parent chain fields for turns/messages: `parent_turn_id`, `parent_message_id`, and `logical_parent_message_id` when rollback/fork needs to preserve ancestry.
- Link every run `thread_id` to a conversation and turn.
- Durable transcript storage in SQLite.
- Transcript message parts for user text, assistant text, tool summaries, interrupt/resume markers, and runtime metadata.
- Accumulate streamed `text_delta` events into assistant transcript messages.
- Persist user messages before run execution starts.
- Store tool results as bounded summaries, not unlimited raw outputs.
- Store hidden thinking separately from visible transcript; hidden thinking is not replayed as assistant answer text.
- Explicit compaction records rather than invisible summary rewrites.
- Tool-output replacement records for large or sensitive tool output: transcript stores a bounded stub/summary plus a Kira-owned replacement reference and hash.
- Fork conversation from a selected message/turn into a new conversation.
- Roll back a conversation to a selected message/turn by moving the active head, without deleting original transcript by default.
- Conversation context packing:
  - active parent chain only;
  - explicit compaction summaries;
  - recent raw turns;
  - bounded tool summaries and replacement stubs when useful;
  - explicit omissions when budget is exceeded.
- Add `ContextItem` kinds for `conversation_history`, `conversation_summary`, `tool_summary`, and `compaction_summary`.
- Transcript summarization using fixture/mock summarizer by default and real provider only when configured.
- Frontend can create/select conversations and keep follow-up prompts in the same conversation.
- `/api/runs` accepts optional `conversation_id` and returns both `conversation_id` and `thread_id`.
- Conversation APIs for list/read/archive/title/transcript/context inspection, fork, rollback, and compact.

Excluded:

- Replacing memory with transcript.
- Automatic promotion of transcript content into project/user memory without Stage 07 approval policy.
- Cross-device/cloud transcript sync.
- Multi-user collaboration.
- Infinite history injection into every prompt.
- Storing raw secrets or raw large tool outputs in transcript.
- Full Git-like branch graph UI in v0. Stage 08 only needs safe fork/rollback primitives and inspectable ancestry.

## Inputs And Dependencies

- Stage 01 local web run shell.
- Stage 04 SQLite run projection, run events, replay, and `thread_id` reliability.
- Stage 05 SSE stream and HITL event semantics.
- Stage 06 ContextItem budget builder and project knowledge context.
- Stage 07 memory model and extraction candidate flow.
- Provider layer with fixture fallback and real provider stream mapping.

## Design

### Object Model

| Object | Purpose |
| --- | --- |
| `conversation_id` | Stable chat/session container shown in the Web UI |
| `turn_id` | One user request and the assistant work that answers it |
| `thread_id` | Single run/graph execution cursor for one assistant attempt |
| `message_id` | Durable transcript message ID |
| `part_id` | Ordered message part for text, tool summary, control marker, or metadata |
| `parent_message_id` | Structural predecessor used to reconstruct active history |
| `active_head_message_id` | Conversation head used for the next prompt's context |
| `forked_from` | Optional source conversation/message reference for branch provenance |

`thread_id` remains the reliable execution cursor. `conversation_id` is the continuity cursor. A conversation may contain many turns, and a turn may have one or more runs if a user retries or resumes.

### Parent Chain And Active Head

Every visible user/assistant transcript message should have a stable `parent_message_id` except the root message. Most conversations form a straight line, but rollback and fork require ancestry:

- `parent_message_id` reconstructs the active history for model input;
- `logical_parent_message_id` preserves original ancestry when a message is copied or replayed after fork/rollback;
- `active_head_message_id` on the conversation points to the message that future turns continue from;
- archived, rolled-back, or forked-away messages remain inspectable but are not injected unless they are on the selected active chain.

The active context builder should walk from `active_head_message_id` back to the root, reverse that list, apply compaction/replacement rules, then pack ContextItems. This avoids accidental context bleed from abandoned branches.

### Transcript Message Shape

```python
class TranscriptMessage(TypedDict, total=False):
    id: str
    conversation_id: str
    turn_id: str
    thread_id: str | None
    parent_message_id: str | None
    logical_parent_message_id: str | None
    role: Literal["user", "assistant", "tool", "system"]
    status: Literal["draft", "streaming", "completed", "error", "cancelled"]
    branch_status: Literal["active", "rolled_back", "fork_source", "archived"]
    parts: list[TranscriptPart]
    created_at: str
    updated_at: str

class TranscriptPart(TypedDict, total=False):
    id: str
    kind: Literal["text", "tool_summary", "tool_replacement", "interrupt", "resume", "error", "compaction", "rollback", "fork", "metadata"]
    text: str
    payload: dict
    visible: bool
    token_estimate: int
```

Hidden thinking is not a normal transcript part. Kira may persist a redacted status/debug record for trace export, but provider reasoning and `<think>` content must not be inserted into visible assistant history or future model input.

### Context Packing

Each new run builds context in this order:

1. System/runtime instructions.
2. Active skill/workflow context.
3. Explicit conversation compaction summaries on the active parent chain.
4. Recent raw transcript tail on the active parent chain.
5. Bounded tool summaries or replacement stubs needed by the active workflow.
6. Project knowledge citations.
7. Memory retrieval.

The exact order can be tuned by the budget builder, but transcript must be a first-class input. Recent user/assistant turns preserve natural dialogue continuity; older turns are summarized to avoid prompt bloat.

Context items:

| Kind | Trust | Contents |
| --- | --- | --- |
| `conversation_history` | `user_supplied` / `runtime_generated` | Recent user and assistant visible messages |
| `conversation_summary` | `runtime_generated` | Rolling summary of older completed turns |
| `compaction_summary` | `runtime_generated` | Explicit compacted span summary with source range and stale flag |
| `tool_summary` | `runtime_generated` | Bounded summaries of relevant prior tool results |

Transcript context is different from memory. It is scoped to a conversation, can be deleted with the conversation, and should not survive as user/project knowledge unless Stage 07 memory approval writes it.

### Explicit Compaction

Compaction is a transcript operation, not an invisible mutation. Kira should create an explicit `compaction` part or system message that records:

- source span: first/last message IDs and turn IDs covered;
- summary text;
- previous summary ID if this compaction updates an earlier summary;
- tail start message ID for recent raw turns preserved outside the summary;
- source hash over covered visible messages and bounded tool summaries;
- provider profile or fixture summarizer used, redacted;
- token estimates before/after;
- stale flag when covered messages are edited, deleted, rolled back, or replaced.

The context builder should prefer the latest non-stale compaction summary for old spans, then append recent raw turns after `tail_start_message_id`. Manual compaction, auto compaction, and overflow-triggered compaction should all produce the same visible data model.

### Summarization

Summaries are generated when the raw transcript exceeds the configured context window or turn count. The summarizer should:

- preserve user goals, constraints, decisions, unresolved questions, selected skill, project root, and relevant tool outcomes;
- exclude hidden thinking and raw secrets;
- cite the message/turn range it summarizes;
- be deterministic in fixture tests;
- be regenerated or marked stale when edited/deleted transcript messages invalidate it.

### Tool Output Replacement

Tool outputs can be useful for resume and debug, but large outputs destroy context quality. Kira should treat tool output replacement as a first-class transcript operation:

| Field | Meaning |
| --- | --- |
| `replacement_ref` | Kira-owned storage pointer for the original or redacted original, when retained |
| `output_hash` | Hash used to prove the stub corresponds to the stored output |
| `summary` | Model-visible bounded description |
| `omitted_chars` | Number of omitted characters |
| `retention` | `none`, `debug_only`, or `local_blob` |
| `reason` | `too_large`, `secret_guard`, `manual_clear`, or `compaction_prune` |

Provider input should receive the summary/stub, not raw replaced output. Replay/debug export may expose the replacement only through Stage 09 redaction and permission policy.

### Fork And Rollback

Fork and rollback should be safe, local, and explicit:

- `POST /api/conversations/{conversation_id}/fork` creates a new conversation with `forked_from_conversation_id`, `forked_from_message_id`, and a copied or linked active parent chain up to that point.
- `POST /api/conversations/{conversation_id}/rollback` moves `active_head_message_id` back to a selected message/turn, records a rollback marker, and excludes later messages from future context.
- Rollback is non-destructive by default. Deleting transcript content is a separate Stage 09 audited action.
- Retry after rollback creates a new turn whose parent is the rollback head.
- Resume of an interrupted `thread_id` remains tied to its original turn; if the conversation has rolled back past that turn, resume should require explicit user confirmation or return a structured conflict.

### Run Flow

1. Frontend creates or selects a `conversation_id`.
2. User submits text.
3. Backend creates a `turn_id`, persists a user transcript message, and creates a run `thread_id`.
4. Context builder walks the active parent chain, applies compaction and replacement rules, loads recent turns, then packs skill/project/memory context.
5. Provider or graph runtime streams KiraEvents.
6. Visible `text_delta` chunks are accumulated into the assistant transcript message.
7. Tool, interrupt, resume, error, cancel, and done events update transcript parts/status.
8. On completion, Kira may update rolling summary and Stage 07 memory extraction candidates.
9. If context overflow is detected, Kira creates an explicit compaction record and retries context packing without losing provenance.

### Public Interfaces

| Endpoint | Responsibility |
| --- | --- |
| `POST /api/conversations` | Create an empty local conversation |
| `GET /api/conversations` | List local conversations with latest status/title/time |
| `GET /api/conversations/{conversation_id}` | Read conversation metadata |
| `PATCH /api/conversations/{conversation_id}` | Rename/archive/restore a conversation |
| `POST /api/conversations/{conversation_id}/fork` | Fork from a selected message/turn into a new conversation |
| `POST /api/conversations/{conversation_id}/rollback` | Move active head to a selected message/turn and record a rollback marker |
| `POST /api/conversations/{conversation_id}/compact` | Create or refresh an explicit compaction summary |
| `GET /api/conversations/{conversation_id}/transcript` | Read ordered messages and parts with pagination |
| `GET /api/conversations/{conversation_id}/context` | Explain which transcript summary/history/tool summaries would be injected |
| `POST /api/runs` | Accept optional `conversation_id`; create one if omitted; return `conversation_id`, `turn_id`, and `thread_id` |

### Storage Additions

| Table | Purpose |
| --- | --- |
| `conversations` | local conversation metadata, title, status, archived flag, timestamps |
| `conversation_turns` | turn IDs linked to conversation, user message, run IDs, status |
| `transcript_messages` | ordered user/assistant/tool/system messages with parent/logical parent and branch status |
| `transcript_parts` | message parts with visible flag, kind, bounded text, redacted payload |
| `conversation_summaries` | rolling summaries with covered turn range and source hash |
| `conversation_run_links` | mapping between conversation, turn, and `thread_id` |
| `conversation_branches` | fork/rollback provenance and active head transitions |
| `tool_output_replacements` | replacement refs, hashes, summaries, omitted counts, and retention policy |
| `transcript_context_traces` | included/truncated/omitted history for each run |

### Frontend Behavior

Stage 08 only needs functional continuity, not final visual polish:

- New conversation starts an empty transcript.
- Submitting follow-up prompts reuses the selected `conversation_id`.
- The workbench shows prior visible messages before the current stream.
- The task rail can list conversations using latest title/status.
- Context inspector shows transcript history/summary/tool-summary inclusion.
- Context inspector shows active head, compaction summaries, replacement stubs, and omitted inactive branches.
- Basic fork/rollback controls can be developer-facing in Stage 08; Stage 10 polishes them.
- Retry/resume stays linked to the same turn/conversation.

## OpenSpec Slice Recommendation

Keep Stage 08 as one roadmap stage, but implement it through focused OpenSpec changes:

| Slice | Scope |
| --- | --- |
| `stage-08a-transcript-core` | conversation/turn/message/part tables, parent chain, run linkage, visible text persistence, context trace |
| `stage-08b-context-compaction` | explicit compaction records, summary refresh/stale rules, tool output replacement, overflow handling |
| `stage-08c-fork-rollback` | fork API, rollback API, active head semantics, inactive branch omission, resume conflict handling |

## Implementation Tasks

1. Add conversation, turn, transcript, summary, and run-link SQLite tables.
2. Add parent chain fields, `active_head_message_id`, fork provenance, branch status, and transcript metadata to run creation and projection records.
3. Extend `POST /api/runs` to accept optional `conversation_id` and return `conversation_id`/`turn_id`.
4. Add conversation list/read/update/transcript/context APIs.
5. Persist user transcript message before provider/graph execution starts.
6. Accumulate `text_delta` into assistant transcript messages and mark terminal status on `done`/`error`/cancel.
7. Persist bounded tool summaries, interrupt/resume markers, and errors as transcript parts.
8. Add tool-output replacement records and replacement stubs for context.
9. Add transcript ContextItem kinds and budget priorities.
10. Implement active-chain context builder with recent raw turns, explicit compaction summaries, replacement stubs, tool summaries, and omission trace.
11. Add deterministic fixture summarizer and optional real-provider summarizer.
12. Add explicit compact endpoint and overflow-triggered compaction path.
13. Add fork and rollback endpoints with active-head updates and structured resume conflicts.
14. Wire memory extraction to completed transcript summaries without automatic writes.
15. Update frontend state so selected conversation persists across follow-up runs.
16. Add transcript/context inspector UI for included history, compaction, replacement, and inactive branches.
17. Add tests for follow-up prompts, parent-chain reconstruction, fork isolation, rollback active-head context, budget truncation, summary refresh, replacement stubs, no hidden-thinking leakage, retry/resume linkage, and transcript deletion/archive behavior.

## Validation

- A second prompt in the same `conversation_id` sees relevant prior user and assistant messages.
- A new conversation does not receive another conversation's transcript.
- `thread_id` resume still works for an interrupted run inside a conversation.
- Visible assistant text is persisted, but `thinking_delta` is not replayed as assistant answer text.
- Large transcripts are summarized/truncated with explicit context trace omissions.
- Compaction appears as an explicit transcript/context artifact with source range and stale status.
- Forked conversations inherit history only up to the selected message/turn.
- Rolled-back messages remain inspectable but are excluded from future context.
- Tool results stored in transcript are bounded summaries, not raw unbounded outputs.
- Replaced tool outputs inject only stubs/summaries and can be audited by hash/reference.
- Memory extraction can use the completed transcript, but no memory is written without Stage 07 policy.
- Frontend can refresh and still display the conversation transcript from backend state.

## Exit Criteria

- Kira supports real multi-turn local conversations.
- Transcript, memory, project knowledge, and graph checkpoint each have separate responsibilities.
- Follow-up questions work without manually copying prior context.
- Context inspection explains which transcript history, compaction summaries, replacement stubs, and inactive branches reached or did not reach the model.

## Deferred Work

- Cross-device sync, collaborative conversations, import/export formats, and user-level conversation search are future product decisions.
- Product-grade conversation UI polish lands in Stage 10.
