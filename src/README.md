# Shared Source

This directory is reserved for cross-cutting source files that are not owned exclusively by the Python server or the TypeScript web app.

Stage 01 use:

- `schemas/kira-event.schema.json` defines the provider-neutral SSE event envelope.
- `schemas/stage-01-fixtures.json` documents deterministic fixture scripts used by backend and frontend tests.

Kira events use provider-neutral envelopes. Later stages extend the event type set for graph tool activity, retries, checkpoints, HITL resume, done, and error while keeping provider-specific payloads out of the shared contract.

Stage 02 use:

- `schemas/tool-result.schema.json` defines the normalized tool result envelope.
- `schemas/stage-02-tools.example.json` documents the five built-in Stage 02 tools and representative success/error payloads.

Stage 02 tools are read-only for project files. Python execution is controlled Python subprocess execution, not a shell. Retrieval indexing, memory, and HITL resume behavior remain later-stage work.

Real provider use:

- `schemas/provider-metadata.schema.json` defines frontend-safe provider selection metadata.
- Provider metadata must never include raw API keys. If an API key indicator is present, it must be redacted.

Stage 03 use:

- `schemas/skill-metadata.schema.json` defines frontend-safe workflow-capable skill metadata.
- Graph state and skill metadata must never include raw provider config or raw API keys.

Stage 04 use:

- `schemas/run-state.schema.json` defines frontend-safe run projection metadata.
- `schemas/run-replay.schema.json` defines read-only replay/debug export payloads.
- `schemas/failure-metadata.schema.json` defines stable failure class metadata.
- `schemas/side-effect-ledger.schema.json` defines bounded side-effect ledger summaries.
- Checkpoints, projections, replay exports, provider attempts, repair notes, and ledger summaries must never include raw API keys.

Stage 05 use:

- `schemas/interrupt-payload.schema.json` defines the frontend-safe HITL interrupt envelope.
- `schemas/resume-request.schema.json` defines human decision payloads posted to the resume endpoint.
- `schemas/resume-result.schema.json` defines the resume response envelope and continuation events.
- `schemas/kira-event.schema.json` now includes graph/tool/retry/checkpoint/interrupt/resume event types.
- HITL payloads must stay compact and redacted; raw LangGraph events, raw provider config objects, and API keys must never cross the shared contract.

Stage 06 use:

- `schemas/skill-package.schema.json` defines frontend-safe local skill package metadata from `SKILL.md` and optional `skill.yaml`.
- `schemas/context-item.schema.json` defines typed, budgeted skill/project ContextItems and citations.
- `schemas/run-context-trace.schema.json` defines the run context trace used by the UI to show included, truncated, and omitted context.
- `schemas/project-knowledge.schema.json` defines project index status and retrieval result envelopes.
- Retrieved project content must be labeled as untrusted data and must not expand tool permissions, provider configuration, or system instructions.

Stage 07 use:

- `schemas/memory.schema.json` defines memory records, scopes, types, statuses, retrieval results, score reasons, guard results, and extraction candidates.
- `schemas/context-item.schema.json` now includes `memory` ContextItems and memory citation metadata alongside Stage 06 project citations.
- `schemas/run-context-trace.schema.json` can include memory retrieval summaries, citation IDs, selected memory IDs, omitted counts, and score explanations.
- Memory contracts must not expose raw API keys, bearer tokens, cookies, private keys, `.env` secrets, provider config, provider errors, or high-risk personal/customer data.

Stage 08a use:

- `schemas/conversation-transcript.schema.json` defines local conversations, turns, run links, transcript messages, transcript parts, and transcript context traces.
- `schemas/run-create.schema.json` defines run creation request/response fields, including optional `conversation_id` input and `conversation_id`/`turn_id` output.
- `schemas/context-item.schema.json` now includes `conversation_history` and `tool_summary` ContextItems with transcript citation metadata.
- `schemas/run-context-trace.schema.json` can include transcript context trace metadata alongside skill, project, and memory traces.
- `schemas/run-state.schema.json` includes frontend-safe conversation, turn, message, transcript status, and transcript part references.
- `schemas/stage-08-transcript.example.json` contains representative conversation, transcript, run response, and mixed context trace fixtures.
- Transcript is local conversation history. It remains separate from Stage 07 memory and from `thread_id`, which is still the execution/replay/resume cursor.

Stage 08b use:

- `schemas/compaction-summary.schema.json` defines explicit conversation compaction summaries, source ranges, hashes, stale state, summarizer metadata, and tail boundaries.
- `schemas/tool-output-replacement.schema.json` defines frontend-safe replacement stubs for oversized or sensitive tool output. Stage 08b exposes metadata, hashes, summaries, and redacted references only.
- `schemas/compact-conversation.schema.json` defines the manual compact API request/response and configurable overflow thresholds.
- `schemas/context-item.schema.json` now includes `conversation_summary` and `compaction_summary` ContextItems.
- `schemas/stage-08b-context-compaction.example.json` contains representative manual compaction and replacement-stub fixtures.
- Compaction summaries and replacement stubs stay scoped to transcript context. They do not create memory records and do not expose raw retained output blobs.

### Stage 08c Fork/Rollback

- `schemas/conversation-branching.schema.json` defines branch records, active-head transitions, and fork/rollback operation responses.
- `schemas/conversation-transcript.schema.json` includes fork source fields, transcript branch status, branch records, and active-head transition arrays.
- `schemas/run-context-trace.schema.json` and `schemas/run-state.schema.json` include branch metadata and the active head observed when a run was created.
- `schemas/stage-08c-branching.example.json` contains a representative fork transcript with inherited and active branch messages.
- Fork/rollback records are transcript metadata only. They do not create memory records, provider calls, tool calls, compaction summaries, or replacement blobs.

### Stage 09 Safety/Observability

- `schemas/permission-decision.schema.json` defines local permission decisions and approval/denial metadata.
- `schemas/audit-record.schema.json` defines redacted audit records for provider, workflow, tool, project, memory, transcript, HITL, and replacement operations.
- `schemas/doctor-diagnostics.schema.json` defines local readiness checks and remediation hints.
- `schemas/trace-export.schema.json` defines bounded read-only trace exports for run, conversation, project, and memory scopes.
- `schemas/replacement-inspection.schema.json` defines policy-gated replacement inspection responses.
- `schemas/stage-09-safety-observability.example.json` documents no-secret fixtures for audit, doctor, trace, and replacement inspection.
- Stage 09 schemas require redaction for API keys, hidden thinking, raw provider config, raw replacement blobs, and high-risk sensitive fields before frontend display or export.
