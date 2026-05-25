## Context

Kira currently treats a normal workbench run as an independent prompt. Stage 04 made `thread_id` durable for one run lineage and Stage 05 uses that lineage for HITL resume, but `thread_id` is not a multi-turn chat container. Stage 07 added memory, but memory is curated durable context and explicitly not transcript.

The Stage 08 roadmap splits transcript work into focused slices. This change implements the 08a core: conversation identity, transcript persistence, run linkage, recent history ContextItems, and frontend continuity. Later slices own explicit compaction, tool-output replacement blobs, fork/rollback, and safety/observability polish.

Existing constraints still apply: `server/`, `web/`, and `src/` remain the only implementation roots; provider config stays redacted; hidden thinking is never visible assistant transcript; project files remain read-only; no general shell or LangChain memory is introduced.

## Goals / Non-Goals

**Goals:**

- Introduce `conversation_id` for multi-turn continuity while preserving `thread_id` for run/resume reliability.
- Persist user messages before run execution and persist visible assistant responses from streamed events.
- Store bounded transcript markers for tool summaries, interrupts/resumes, errors, and terminal status.
- Build provider input from recent visible transcript on the active parent chain through `ContextItem` packing.
- Expose conversation create/list/read/update/transcript/context APIs.
- Update the workbench so follow-up runs reuse the selected conversation and prior visible transcript is restored from backend state.
- Add tests proving "你好" followed by "我刚刚和你说什么了" can see the prior user turn when the same conversation is active.

**Non-Goals:**

- No automatic transcript-to-memory writes; Stage 07 candidate approval remains the memory boundary.
- No explicit compaction summaries, stale summary refresh, or overflow-triggered summarizer in this slice.
- No fork/rollback UI or API in this slice beyond storing parent links needed for future work.
- No raw large tool-output replacement blob store; this slice stores only bounded summaries/markers.
- No Stage 09 audit/doctor/trace export hardening.
- No Stage 10 visual redesign.

## Decisions

### Separate `conversation_id` From `thread_id`

`conversation_id` is the continuity cursor shown in the web app. `thread_id` remains the execution cursor used by SSE, replay, locks, checkpoints, and HITL resume.

Alternative considered: reuse `thread_id` for chat continuation. Rejected because retry/resume and multi-turn chat have different lifecycles; a conversation can contain many runs, while a thread belongs to one run lineage.

### Store Transcript As Messages And Parts

The backend will store conversations, turns, transcript messages, and transcript parts in SQLite. A user turn creates a user message. A run creates or updates an assistant message. Streamed visible text is accumulated into text parts; tool/HITL/error metadata is represented by bounded non-answer parts.

Alternative considered: store a flat transcript blob per conversation. Rejected because it makes parent-chain context, future fork/rollback, bounded tool summaries, and safe redaction harder to implement and test.

### Parent Chain Is The Context Source

Each visible transcript message links to a parent message. Stage 08a mostly creates linear chains, but using parent links now avoids a later migration when fork/rollback lands. The active conversation head points to the message future turns continue from.

Alternative considered: use timestamp order only. Rejected because rolled-back or future forked messages would accidentally leak into prompt context.

### Recent History Enters Through ContextItems

The context builder will create `conversation_history` ContextItems from recent visible user/assistant turns and optional bounded `tool_summary` items. Those items flow through the same budget packer as skills, project context, and memory.

Alternative considered: concatenate transcript directly into the prompt. Rejected because it bypasses budget traces, trust labels, omission reporting, and the existing inspectable context path.

### Hidden Thinking Is Stored Only As Debug Metadata Or Ignored

`thinking_delta` remains a status/debug stream event. It is not appended to visible assistant transcript and is not injected as conversation history.

Alternative considered: keep hidden thinking in transcript for local debugging. Rejected for the core transcript contract because it would blur visible assistant response with private reasoning/status content and could pollute future model input.

### Stage 08a Uses Bounded Core Without Compaction

This slice will use recent-turn limits and budget omission records. Explicit compaction and summarization are deferred to Stage 08b, because they need source-range hashes, stale rules, replacement references, and summarizer policy.

Alternative considered: implement all Stage 08 transcript behavior at once. Rejected because it would mix core continuity with compaction and branch semantics, making review and regression risk too high.

## Risks / Trade-offs

- [Risk] Transcript context could grow quickly before compaction exists. → Mitigation: enforce recent-turn, character, and ContextItem budget limits; record omissions in the context trace.
- [Risk] Assistant chunks could be duplicated on SSE reconnect or replay. → Mitigation: append transcript text only during the active executor path and make reconnect replay read-only for transcript state.
- [Risk] Conversation history could leak across conversations. → Mitigation: context builder must require `conversation_id` and active head; tests cover isolation.
- [Risk] Hidden thinking may accidentally enter transcript through generic event handling. → Mitigation: event-to-transcript mapping explicitly excludes `thinking_delta` from visible transcript and provider history.
- [Risk] HITL resume could be confused with starting a new conversation turn. → Mitigation: resume continues the existing `thread_id` and turn; new `/api/runs` calls create new turns.
- [Risk] Future fork/rollback needs ancestry fields not used heavily in 08a. → Mitigation: add parent/logical-parent fields now but keep APIs out of scope until 08c.

## Migration Plan

1. Add idempotent SQLite migrations for conversation and transcript tables.
2. Extend shared schemas and TypeScript types before API integration.
3. Add backend transcript service with repository-level tests.
4. Integrate run creation, event streaming, resume, cancel, state, and replay with transcript linkage.
5. Add conversation API routes.
6. Update frontend API client and workbench selected conversation state.
7. Add backend/frontend regression tests and OpenSpec validation.

Rollback strategy: the new tables are additive. Existing runs without `conversation_id` remain readable. If transcript integration is disabled, `/api/runs` can continue creating standalone runs while leaving conversation tables unused.

## Open Questions

- Should the first user prompt become the default conversation title immediately, or should title generation wait for Stage 08b summarization?
- What default recent-turn limit should ship before compaction exists: by turn count, estimated tokens, characters, or combined budget?
- Should archived conversations remain available to memory extraction, or should extraction require active conversations only?
