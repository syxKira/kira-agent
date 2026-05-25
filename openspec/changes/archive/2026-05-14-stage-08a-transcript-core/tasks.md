## 1. Shared Contracts

- [x] 1.1 Add shared JSON schemas for conversation summaries, turns, transcript messages, transcript parts, conversation run links, and transcript context traces.
- [x] 1.2 Extend shared run request/response schemas to include optional `conversation_id` input and `conversation_id`/`turn_id` output.
- [x] 1.3 Extend shared ContextItem schemas with `conversation_history` and `tool_summary` kinds plus transcript reference metadata.
- [x] 1.4 Export frontend TypeScript types for conversations, turns, transcript messages/parts, transcript context traces, and run conversation metadata.
- [x] 1.5 Add schema validation fixtures for a conversation, transcript, run response, and mixed context trace containing conversation, project, and memory items.

## 2. Storage And Repository

- [x] 2.1 Add SQLite migrations for `conversations`, `conversation_turns`, `transcript_messages`, `transcript_parts`, `conversation_run_links`, and `transcript_context_traces`.
- [x] 2.2 Add migration tests proving Stage 04 run tables, Stage 06 project tables, and Stage 07 memory tables remain readable after transcript migrations.
- [x] 2.3 Implement backend transcript repository functions for create/list/read/update/archive conversations.
- [x] 2.4 Implement turn creation and `conversation_id`/`turn_id`/`thread_id` run-link persistence.
- [x] 2.5 Implement transcript message creation with role, status, parent message ID, logical parent message ID, active branch status, and timestamps.
- [x] 2.6 Implement transcript part append/update helpers with bounded text, visible flags, kind metadata, redacted payloads, and ordering.
- [x] 2.7 Implement active head update rules for user and assistant messages in the linear Stage 08a chain.
- [x] 2.8 Add repository tests for conversation CRUD, turn/run links, message parent chain, active head updates, bounds, and redaction.

## 3. Backend Run Integration

- [x] 3.1 Extend `POST /api/runs` request handling to accept optional `conversation_id`, create a conversation when omitted, and reject unknown/archived conversation IDs.
- [x] 3.2 Persist the user transcript message before provider, graph, project retrieval, or memory retrieval execution starts.
- [x] 3.3 Return `conversation_id` and `turn_id` in run creation responses without breaking existing callers.
- [x] 3.4 Create or reserve the assistant transcript message for the run and link it to the turn.
- [x] 3.5 Accumulate visible `text_delta` chunks into assistant transcript text in event order.
- [x] 3.6 Exclude `thinking_delta` content from visible transcript and future conversation history.
- [x] 3.7 Persist bounded tool result, side-effect reuse, interrupt, resume, error, cancel, and done transcript parts/status updates.
- [x] 3.8 Ensure SSE reconnect/replay does not duplicate transcript text or transcript parts.
- [x] 3.9 Ensure HITL resume continues the existing `thread_id` and turn without creating a new user message.
- [x] 3.10 Add backend tests for one-shot runs, same-conversation follow-up runs, fixture fallback, provider runs with mocked stream, HITL resume linkage, error/cancel status, and no duplicate transcript on reconnect.

## 4. Conversation APIs

- [x] 4.1 Add `POST /api/conversations` for creating an empty local conversation.
- [x] 4.2 Add `GET /api/conversations` for listing active conversations with latest title/status/time metadata.
- [x] 4.3 Add `GET /api/conversations/{conversation_id}` for reading conversation metadata.
- [x] 4.4 Add `PATCH /api/conversations/{conversation_id}` for title update, archive, and restore metadata changes.
- [x] 4.5 Add `GET /api/conversations/{conversation_id}/transcript` with bounded ordered message/part output.
- [x] 4.6 Add `GET /api/conversations/{conversation_id}/context` showing eligible transcript ContextItems for the next run.
- [x] 4.7 Add API tests for create/list/read/update/archive/transcript/context, not-found errors, archived conversation rejection, and conversation isolation.

## 5. Conversation Context Builder

- [x] 5.1 Implement active-parent-chain traversal for the selected conversation.
- [x] 5.2 Convert recent visible user and assistant messages into `ContextItem(kind="conversation_history")`.
- [x] 5.3 Convert bounded prior tool summaries into `ContextItem(kind="tool_summary")` when eligible.
- [x] 5.4 Add deterministic priority and budget-cost handling for conversation history in `pack_context`.
- [x] 5.5 Record transcript context traces with included, truncated, and omitted message/part IDs, turn IDs, reasons, and budget costs.
- [x] 5.6 Integrate conversation ContextItems before provider input assembly for direct provider runs and skill graph runs.
- [x] 5.7 Keep transcript context distinct from memory and do not create memory records from transcript completion.
- [x] 5.8 Add tests for "hello" then "what did I just say" in one conversation, separate conversation isolation, budget omissions, mixed skill/project/memory/history context, tool summary bounds, and hidden-thinking exclusion.

## 6. State And Replay

- [x] 6.1 Extend run state projection with `conversation_id`, `turn_id`, user message ID, assistant message ID, and transcript status.
- [x] 6.2 Extend replay/debug export with frontend-safe conversation/turn/message references.
- [x] 6.3 Ensure replay/debug export reads transcript records without creating new messages, parts, context traces, provider calls, tool calls, memory records, or retrieval traces.
- [x] 6.4 Add tests for state/replay transcript linkage, read-only replay behavior, and secret redaction in transcript summaries.

## 7. Frontend Workbench

- [x] 7.1 Add frontend API client functions for conversation create/list/read/update, transcript read, and context inspect.
- [x] 7.2 Add selected conversation state to the workbench and pass `conversation_id` on follow-up run creation.
- [x] 7.3 Update run response handling to store returned `conversation_id` and `turn_id`.
- [x] 7.4 Load and render prior visible transcript messages for the selected conversation before current stream events.
- [x] 7.5 Add functional conversation list/create/select controls in the existing inspector or side surface without Stage 10 visual redesign.
- [x] 7.6 Update context inspector to show conversation history and tool summary ContextItems with turn/message IDs and omission metadata.
- [x] 7.7 Ensure hidden thinking remains a status row during live streams and never appears as restored assistant transcript text.
- [x] 7.8 Add frontend tests for first-run conversation creation, follow-up run reusing conversation ID, transcript restore, conversation switching isolation, context inspector history items, and no-secret/no-thinking DOM rendering.

## 8. Documentation And Verification

- [x] 8.1 Document transcript versus memory versus `thread_id` responsibilities in README and server/web/src docs.
- [x] 8.2 Document new conversation API endpoints and run payload/response fields.
- [x] 8.3 Run backend unit and integration tests for `server/`.
- [x] 8.4 Run shared schema validation for `src/`.
- [x] 8.5 Run frontend typecheck and tests for `web/`.
- [x] 8.6 Run `openspec validate "stage-08a-transcript-core" --strict`.
- [x] 8.7 Run `openspec status --change "stage-08a-transcript-core"` and confirm the change is ready for apply.
