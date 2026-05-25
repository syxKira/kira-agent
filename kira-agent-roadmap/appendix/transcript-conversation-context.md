# Appendix: Transcript And Conversation Context

Transcript is Kira's short-term conversational truth. It is the ordered record of what the user said, what the assistant visibly answered, which tools were summarized, and which human decisions occurred inside one local conversation.

## Transcript Is Not

- not memory;
- not project search;
- not graph checkpoint state;
- not hidden chain-of-thought;
- not an unlimited prompt dump;
- not a place for secrets or unbounded raw tool output.

## Identity Model

| ID | Meaning |
| --- | --- |
| `conversation_id` | Multi-turn chat/session container |
| `turn_id` | One user request and the assistant work that answers it |
| `thread_id` | One reliable graph/provider run cursor |
| `message_id` | One durable user/assistant/tool/system transcript message |
| `part_id` | One ordered message part |
| `parent_message_id` | Structural predecessor used to reconstruct active history |
| `logical_parent_message_id` | Original predecessor preserved across fork, retry, or rollback replay |
| `active_head_message_id` | Conversation head used for future context |

`conversation_id` carries continuity. `thread_id` carries execution reliability. Mixing them makes follow-up chat and resume/replay both harder to reason about.

## Parent Chain Rules

- Context is built from the active parent chain, not from every row in timestamp order.
- Fork and rollback update the active head; they do not need to delete old messages.
- Messages outside the active chain are inspectable but omitted from provider input by default.
- A resume for a run outside the active chain must either ask for confirmation or fail with a structured conflict.

## Injection Rules

- Recent visible turns can be injected as `ContextItem(kind="conversation_history")`.
- Older turns should be summarized as `ContextItem(kind="conversation_summary")` or `ContextItem(kind="compaction_summary")`.
- Prior tool results should be summarized as `ContextItem(kind="tool_summary")`.
- Replaced tool outputs inject only bounded stubs/summaries, never raw replaced content.
- Hidden thinking must not be injected as conversation history.
- Every run should expose a trace showing included, truncated, and omitted transcript context.
- Transcript context is scoped to its conversation and must not leak across conversations.

## Explicit Compaction Rules

Compaction should be represented as a transcript artifact with source range, summary, tail boundary, source hash, token estimates, summarizer metadata, and stale status. It should not silently rewrite history.

Conversation summaries and compaction summaries should preserve:

- user goals and constraints;
- decisions and approvals;
- unresolved questions;
- active project root and selected skills;
- important bounded tool outcomes;
- pointers to message/turn ranges covered by the summary.

Summaries should exclude:

- secrets and raw credentials;
- hidden thinking;
- unbounded raw tool output;
- content from archived/deleted messages.

## Tool Output Replacement

Tool output replacement records should store a model-visible stub plus metadata:

- replacement reference in Kira-owned storage when retention allows it;
- hash of original or redacted original;
- summary;
- omitted character count;
- reason such as `too_large`, `secret_guard`, `manual_clear`, or `compaction_prune`;
- retention policy.

Provider input receives the stub/summary. Debug export may resolve the replacement only through Stage 09 redaction and permission policy.

## Relation To Memory

Memory may be extracted from transcript after a run, but only as a candidate governed by Stage 07 policy. Transcript is the source record for a conversation; memory is a curated durable fact or preference that may outlive that conversation.
