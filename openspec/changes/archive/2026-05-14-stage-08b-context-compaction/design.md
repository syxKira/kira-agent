## Context

Stage 08a introduced durable conversations, turns, parent-linked transcript messages, visible assistant text persistence, basic tool summaries, and conversation history ContextItems. That makes short follow-up prompts work, but long conversations still degrade by dropping or truncating older raw history when the context budget is tight.

The Stage 08 roadmap calls for explicit compaction and tool-output replacement before fork/rollback. This change keeps that boundary: it adds summary artifacts and replacement stubs on top of the Stage 08a transcript model, but it does not introduce branch APIs or Stage 09 audit/export policy.

Existing constraints still apply: implementation stays in `server/`, `web/`, and `src/`; provider config stays redacted; fixture fallback keeps tests deterministic; hidden thinking is never visible transcript or model history; project files remain read-only; no general shell is introduced.

## Goals / Non-Goals

**Goals:**

- Add explicit compaction summaries with source ranges, source hashes, tail boundaries, token estimates, summarizer metadata, and stale status.
- Add a deterministic fixture summarizer and optional real-provider summarizer path using existing provider selection and redaction rules.
- Make long conversations use non-stale summaries for older active-chain spans, plus a recent raw tail, instead of only dropping older messages.
- Add tool-output replacement records that store model-visible stubs/summaries, hashes, omitted counts, retention policy, and redacted references.
- Ensure provider input receives bounded summary/stub ContextItems, not raw replaced tool output.
- Expose compaction and replacement metadata through conversation APIs, run context traces, state/replay summaries, shared schemas, and minimal workbench inspector UI.
- Keep transcript separate from Stage 07 memory and do not automatically write memories from summaries.

**Non-Goals:**

- No Stage 08c fork/rollback endpoints, inactive branch controls, or resume conflict semantics.
- No Stage 09 permission policy for resolving retained replacement blobs or full audit/doctor/trace export.
- No Stage 10 visual redesign.
- No cloud sync, multi-user transcript collaboration, vector database, project mutation tools, general shell tool, or automatic transcript-to-memory promotion.
- No hidden thinking persistence as visible transcript or future provider conversation history.

## Decisions

### Compaction Is A First-Class Transcript Artifact

Compaction will be stored as explicit records linked to a conversation, source message/turn range, source hash, and tail start. The original transcript messages remain intact.

Alternative considered: overwrite older transcript messages with a rolling summary. Rejected because it destroys provenance, makes stale detection hard, and conflicts with Stage 08 fork/rollback and Stage 09 audit goals.

### Use Fixture Summarization By Default

The backend will expose a summarizer boundary. Tests and default local runs use a deterministic fixture summarizer. If valid real provider config exists and the request/policy allows it, a real provider can generate a summary through the existing redacted provider layer.

Alternative considered: require a real LLM for compaction. Rejected because Stage 08b must be testable and usable without an API key.

### Stale Beats Mutation

When covered source messages or replacement records change after a summary is created, the summary is marked stale or omitted from context until refreshed. Stale summaries remain inspectable.

Alternative considered: silently regenerate summaries whenever context is built. Rejected because context inspection and replay must be read-only unless an explicit compaction operation or overflow path is running.

### Context Builder Uses Summary Plus Tail

The active-chain context builder will choose the latest non-stale compaction summary that covers older messages, then append recent visible raw user/assistant messages after the summary tail boundary. If no valid summary exists, the Stage 08a recent-history behavior remains the fallback.

Alternative considered: include both summary and all covered raw messages. Rejected because it wastes budget and can create contradictory duplicate context.

### Replacement Stubs Are Provider-Facing, Raw Outputs Are Not

Large or sensitive tool outputs will be represented by a replacement record and transcript part containing a bounded summary/stub. The provider receives only that bounded stub through `tool_summary` or replacement metadata. Raw retained content, if any, is local-only and not exposed by Stage 08b APIs.

Alternative considered: store and inject raw tool output behind a larger budget. Rejected because it creates prompt bloat and increases secret-leak risk.

### Replay Is Read-Only

State and replay may include saved compaction/replacement summaries, IDs, stale flags, hashes, and omitted counts. They must not regenerate summaries, resolve local blobs, append transcript parts, call providers, call tools, or create memory records.

Alternative considered: rebuild the latest transcript context during replay. Rejected because replay/debug export must reflect saved run state and avoid side effects.

## Risks / Trade-offs

- [Risk] Fixture summaries may be lower quality than real-provider summaries. -> Mitigation: keep fixture deterministic for tests and allow optional real summarizer when valid config exists.
- [Risk] A stale summary could be used after transcript edits or replacement refresh. -> Mitigation: compute and store source hashes; context builder omits stale summaries and traces the stale reason.
- [Risk] Overflow-triggered compaction could surprise users. -> Mitigation: create explicit compaction records, expose them in context trace/transcript, and never delete source messages.
- [Risk] Tool replacement can hide useful details. -> Mitigation: preserve hash, omitted count, reason, bounded summary, and frontend-safe reference metadata; raw resolution remains a Stage 09 policy decision.
- [Risk] Context ordering may become harder to inspect. -> Mitigation: trace included, truncated, omitted, stale, and replaced transcript items with IDs and budget costs.
- [Risk] Summary generation can fail. -> Mitigation: fall back to Stage 08a recent-history behavior and produce structured compaction errors without failing the local web loop.

## Migration Plan

1. Add shared schemas for compaction summaries, replacement records, summary ContextItems, and example fixtures.
2. Add idempotent SQLite migrations for compaction summaries and tool-output replacement records.
3. Implement transcript compaction and replacement repository/service methods.
4. Implement deterministic fixture summarizer and optional provider summarizer behind the existing provider layer.
5. Integrate compaction and replacement selection into active-chain context building and run context traces.
6. Add manual compact API and overflow-triggered compaction path with structured fallback.
7. Extend state/replay and frontend workbench inspector with summary/replacement metadata.
8. Add backend, frontend, schema, and OpenSpec validation coverage.

Rollback strategy: migrations are additive. Existing Stage 08a transcript records remain readable. If compaction is disabled, the context builder can ignore compaction/replacement records and continue using the Stage 08a recent-history path.

## Open Questions

- What default thresholds should trigger overflow compaction before Stage 10 exposes richer configuration: message count, estimated tokens, character count, or a combined policy?
- Should manual compaction always use fixture summarization unless the user explicitly requests a real provider summarizer?
- Should replacement records retain redacted local blobs in Stage 08b, or only store stubs and hashes until Stage 09 defines resolution policy?
