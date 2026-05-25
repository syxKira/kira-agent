# local-run-api Specification

## Purpose
TBD - created by archiving change stage-01-local-web-foundation. Update Purpose after archive.
## Requirements
### Requirement: Create local runs

The system SHALL expose a FastAPI `POST /api/runs` endpoint that creates a Stage 01 local run using in-memory state and returns a unique `thread_id`.

#### Scenario: Run creation returns thread identifier

- **WHEN** a client posts a valid Stage 01 run request with prompt text and an optional fixture script name
- **THEN** the response includes a unique `thread_id`, initial run status, and enough metadata for the frontend to open the event stream

#### Scenario: Run creation does not require network credentials

- **WHEN** a client creates a run using the fixture provider
- **THEN** the backend does not require external network access or an API key

### Requirement: Stream run events over SSE

The system SHALL expose `GET /api/runs/{thread_id}/events` as an SSE endpoint for normalized Stage 01 run events.

#### Scenario: Existing run streams events

- **WHEN** a client opens the SSE endpoint for an existing `thread_id`
- **THEN** the backend streams ordered events with `type`, `thread_id`, `seq`, and `data` fields

#### Scenario: Missing run returns an API error

- **WHEN** a client opens the SSE endpoint for an unknown `thread_id`
- **THEN** the backend returns a clear not-found API error instead of starting an implicit run

### Requirement: Limit Stage 01 persistence

The system SHALL keep Stage 01 run state in process memory and SHALL NOT add checkpoint, resume, replay, lock, idempotency, or side-effect ledger behavior.

#### Scenario: Stage 04 behavior remains unavailable

- **WHEN** Stage 01 run endpoints are implemented
- **THEN** no checkpoint, resume, replay, run-lock, idempotency, or side-effect-ledger endpoint is exposed

### Requirement: Document local development commands

The system SHALL document how to start the backend and frontend locally for Stage 01.

#### Scenario: Developer follows startup instructions

- **WHEN** a developer follows the documented backend and frontend commands
- **THEN** the FastAPI app and Vite app start independently and the frontend can call the local API

### Requirement: Resume interrupted local runs

The system SHALL expose `POST /api/runs/{thread_id}/resume` for interrupted checkpointed skill graph runs.

#### Scenario: Resume endpoint accepts valid decision

- **WHEN** a client posts a valid resume value for the active pending interrupt on an existing `thread_id`
- **THEN** the backend returns accepted resume metadata and continues graph execution for that `thread_id`

#### Scenario: Resume endpoint rejects missing interrupt

- **WHEN** a client posts to the resume endpoint for a run with no pending interrupt
- **THEN** the backend returns a structured validation or conflict error
- **THEN** no new graph work is scheduled

#### Scenario: Resume endpoint rejects unknown thread

- **WHEN** a client posts to the resume endpoint for an unknown `thread_id`
- **THEN** the backend returns a clear not-found API error

### Requirement: SSE supports reconnect cursors for HITL runs

The system SHALL support `after_seq` cursor replay for HITL graph event streams.

#### Scenario: Reconnect replays missed events

- **WHEN** a client reconnects to `GET /api/runs/{thread_id}/events?after_seq=<n>`
- **THEN** the backend first streams persisted events with sequence greater than `<n>`
- **THEN** missed interrupt, resume, tool, and completion events are delivered without duplicates

#### Scenario: Reconnect does not rerun graph work

- **WHEN** a client reconnects only to read events already persisted for a completed or waiting run
- **THEN** the backend does not invoke provider calls, tools, side effects, or new graph nodes

### Requirement: Run APIs expose safe HITL state

The system SHALL expose pending interrupt and resume status through frontend-safe API payloads without exposing raw secrets or runtime internals.

#### Scenario: Run creation response identifies resume URL

- **WHEN** a skill graph run is created
- **THEN** the run creation response includes enough public metadata for the frontend to stream events and submit resume values when interrupted

#### Scenario: State response includes HITL status

- **WHEN** a run is waiting on human input
- **THEN** the state endpoint reports a waiting status and the current pending interrupt summary
- **THEN** the payload excludes raw API keys and raw provider config objects

### Requirement: Runs accept bounded skill and project context controls

The run creation API SHALL accept frontend-safe controls for explicit skill activation and optional project context retrieval without exposing provider secrets or mutating project files.

#### Scenario: Run opts into project context
- **WHEN** a run request includes a project root and project context query or scope
- **THEN** the backend may retrieve cited project ContextItems within budget before provider input assembly

#### Scenario: Run context controls are redacted
- **WHEN** run creation returns metadata for skill and project context
- **THEN** the response omits raw provider secrets, raw manifest secrets, and unbounded local file contents

### Requirement: Run context trace API is available

The system SHALL expose a frontend-safe run context trace endpoint that shows included, truncated, and omitted ContextItems.

#### Scenario: Context trace returns included and omitted items
- **WHEN** a client requests context trace for a known run
- **THEN** the response includes ContextItem summaries, citations, trust labels, budget costs, truncation status, and omission reasons

#### Scenario: Unknown run context returns not found
- **WHEN** a client requests context trace for an unknown run
- **THEN** the backend returns a structured not-found error

### Requirement: Runs accept memory retrieval controls
The run creation API SHALL accept frontend-safe controls for optional memory retrieval, scope filters, type filters, top-k limits, and memory budget controls.

#### Scenario: Run opts into memory retrieval
- **WHEN** a run request includes memory retrieval controls
- **THEN** the backend retrieves eligible active memories, converts them into ContextItems, and includes them before provider input assembly

#### Scenario: Memory retrieval controls are redacted
- **WHEN** run creation returns metadata for memory context
- **THEN** the response omits raw memory secrets, raw provider secrets, and unbounded memory text

### Requirement: Run context trace exposes memory usage
The run context trace API SHALL show included, truncated, and omitted memory ContextItems, memory citations, and retrieval explanations.

#### Scenario: Context trace returns memory citations
- **WHEN** a client requests context trace for a run that injected memory
- **THEN** the response includes memory IDs, citation IDs, scopes, types, score reasons, trust labels, budget costs, and omission reasons

### Requirement: Memory APIs are local and bounded
The system SHALL expose local memory list, read, create, update, search, candidate, and action APIs with bounded payloads and redacted metadata.

#### Scenario: Memory search API returns explanations
- **WHEN** the frontend calls memory search
- **THEN** the response includes ranked memories, explanations, citations when applicable, omitted counts, and no raw provider secrets

#### Scenario: Unknown memory returns not found
- **WHEN** a client requests or acts on an unknown memory ID
- **THEN** the backend returns a structured not-found error and mutates no memory state

### Requirement: Runs support conversation continuity
The run creation API SHALL accept an optional `conversation_id` and SHALL return `conversation_id` and `turn_id` in the run creation response.

#### Scenario: Run reuses existing conversation
- **WHEN** a client creates a run with an existing active `conversation_id`
- **THEN** the backend creates a new turn in that conversation
- **THEN** the response includes the same `conversation_id`, a new `turn_id`, and a new `thread_id`

#### Scenario: Run creates conversation when omitted
- **WHEN** a client creates a run without `conversation_id`
- **THEN** the backend creates a new conversation
- **THEN** the response includes the created `conversation_id` and `turn_id`

#### Scenario: Unknown conversation is rejected
- **WHEN** a client creates a run with an unknown or archived `conversation_id`
- **THEN** the backend returns a structured validation or not-found error
- **THEN** no provider, graph, tool, memory retrieval, or project retrieval work is started

### Requirement: Conversation APIs are available
The system SHALL expose local API endpoints for creating, listing, reading, updating metadata, reading transcript, and inspecting conversation context.

#### Scenario: Conversation transcript endpoint
- **WHEN** a client requests `GET /api/conversations/{conversation_id}/transcript`
- **THEN** the backend returns bounded ordered transcript messages and parts for that conversation

#### Scenario: Conversation context endpoint
- **WHEN** a client requests `GET /api/conversations/{conversation_id}/context`
- **THEN** the backend returns a frontend-safe explanation of transcript ContextItems that would be eligible for the next run

### Requirement: Run context trace exposes transcript usage
The run context trace API SHALL show included, truncated, and omitted conversation history and tool summary ContextItems.

#### Scenario: Context trace returns transcript items
- **WHEN** a client requests context trace for a run that used conversation history
- **THEN** the response includes conversation ID, turn IDs, message IDs, ContextItem kinds, trust labels, budget costs, and omission reasons

### Requirement: Resume remains thread-scoped inside conversations
The resume API SHALL continue an existing interrupted `thread_id` and SHALL NOT create a new conversation turn.

#### Scenario: Resume keeps turn link
- **WHEN** a client posts a valid resume decision for a run linked to a conversation
- **THEN** the resume event is linked to the existing turn
- **THEN** no new user message is created

### Requirement: Conversation compact API is available
The system SHALL expose a local API endpoint for creating or refreshing compaction summaries for an existing active conversation.

#### Scenario: Compact conversation
- **WHEN** a client posts to `POST /api/conversations/{conversation_id}/compact`
- **THEN** the backend creates or refreshes a compaction summary for eligible active-chain messages
- **THEN** the response includes frontend-safe summary ID, status, source range, tail boundary, stale status, summarizer metadata, token estimates, and omission metadata

#### Scenario: Unknown or archived conversation cannot compact
- **WHEN** a client requests compaction for an unknown or archived conversation
- **THEN** the backend returns a structured not-found or validation error
- **THEN** no provider call, summary record, transcript part, replacement record, memory record, or tool call is created

### Requirement: Conversation context API exposes compaction and replacement decisions
The conversation context API SHALL return frontend-safe summary and replacement metadata for transcript ContextItems eligible for the next run.

#### Scenario: Context endpoint includes summary and replacement metadata
- **WHEN** a client requests `GET /api/conversations/{conversation_id}/context`
- **THEN** the response includes eligible `conversation_summary`, `compaction_summary`, `conversation_history`, and `tool_summary` items
- **THEN** replacement IDs, summary IDs, stale reasons, and budget estimates are visible without raw replaced output

### Requirement: Run creation may trigger explicit overflow compaction
The run creation API SHALL optionally create or refresh compaction summaries when selected conversation history would exceed configured transcript thresholds.

#### Scenario: Overflow compaction occurs before provider input
- **WHEN** a run is created in a long conversation and transcript context exceeds configured thresholds
- **THEN** the backend creates or refreshes an explicit compaction summary before final provider input assembly
- **THEN** the run context trace records the summary and any omitted raw messages

#### Scenario: Overflow compaction fallback is non-fatal
- **WHEN** overflow compaction fails
- **THEN** run creation falls back to bounded Stage 08a recent-history behavior when possible
- **THEN** the run context trace records a structured compaction failure without raw secrets

### Requirement: Run context trace exposes summary and replacement usage
The run context trace API SHALL show included, truncated, omitted, and stale compaction summaries and tool-output replacement stubs.

#### Scenario: Trace returns Stage 08b transcript items
- **WHEN** a run uses compaction summaries or replacement stubs
- **THEN** the context trace includes item kind, summary IDs, replacement IDs, source message/part IDs, stale status, trust labels, budget costs, and omission reasons

### Requirement: Conversation fork API is available
The system SHALL expose a local API endpoint for forking a conversation from a selected active-chain message or turn.

#### Scenario: Fork endpoint creates conversation
- **WHEN** a client posts to `POST /api/conversations/{conversation_id}/fork` with a valid source message or turn
- **THEN** the backend creates a new conversation
- **THEN** the response includes new conversation ID, source conversation ID, source message ID, source turn ID when available, and active head metadata

#### Scenario: Fork endpoint rejects invalid source
- **WHEN** a client forks from an unknown, archived, or inactive source
- **THEN** the backend returns a structured validation or not-found error
- **THEN** no new conversation, transcript part, provider call, tool call, or memory record is created

### Requirement: Conversation rollback API is available
The system SHALL expose a local API endpoint for moving a conversation active head to a selected active-chain message or turn.

#### Scenario: Rollback endpoint moves active head
- **WHEN** a client posts to `POST /api/conversations/{conversation_id}/rollback` with a valid target message
- **THEN** the backend updates the conversation active head
- **THEN** the response includes previous active head, new active head, transition ID, and frontend-safe inactive branch summary

#### Scenario: Rollback endpoint rejects invalid target
- **WHEN** a client rolls back to an unknown, archived, or inactive target
- **THEN** the backend returns a structured validation or not-found error
- **THEN** the conversation active head is unchanged

### Requirement: Run creation honors branch active head
The run creation API SHALL parent new turns from the selected conversation's current active head after fork or rollback.

#### Scenario: Run after rollback excludes abandoned future
- **WHEN** a client creates a run after rollback
- **THEN** the backend links the new user message to the rollback head
- **THEN** run context excludes messages abandoned by the rollback

### Requirement: APIs expose branch context safely
Conversation transcript, conversation context, and run context APIs SHALL expose frontend-safe branch metadata without raw provider secrets or hidden thinking.

#### Scenario: Context endpoint shows inactive branch omission
- **WHEN** a client requests context for a conversation with inactive branch messages
- **THEN** the response explains active head, fork/rollback metadata, included active-chain items, and omitted inactive branch items

### Requirement: Safety and observability APIs are available
The API SHALL expose frontend-safe endpoints for doctor diagnostics, permission decisions or decision previews, audit export, trace export, and replacement inspection where allowed by policy.

#### Scenario: Doctor endpoint
- **WHEN** the frontend calls the doctor endpoint
- **THEN** the API SHALL return component statuses and remediation hints without raw secrets

#### Scenario: Audit endpoint
- **WHEN** the frontend requests audit records with filters
- **THEN** the API SHALL return bounded redacted records and pagination metadata

### Requirement: Safety errors are structured
The API SHALL return structured errors for denied permission, approval required, unsafe provider override, unsafe Python execution, unsafe memory write, unsafe transcript delete, inactive branch resume, and replacement inspection denial.

#### Scenario: Permission denied
- **WHEN** a policy decision denies an action
- **THEN** the response SHALL include a stable code, message, reasons, redacted subject metadata, and no raw secret values

### Requirement: Trace and audit exports are read-only
Doctor, audit, and trace export endpoints SHALL NOT trigger providers, execute tools, refresh retrieval, mutate memory, mutate transcripts, acquire run locks, or advance event streams.

#### Scenario: Export replay facts
- **WHEN** a run trace export is requested
- **THEN** the API SHALL return saved durable facts and SHALL NOT append new run events

