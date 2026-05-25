## Context

Kira already has provider selection, fixture fallback, Stage 02 tools, skill-driven LangGraph runs, durable run storage, HITL resume, skill packages, project knowledge retrieval, and ContextItem budgeting. The remaining gap is durable learned context: user preferences, project decisions, workflow lessons, and facts that are useful across runs but are not current project file evidence.

Memory must remain distinct from transcript history, project knowledge, skill documentation, provider config, and audit. Project knowledge is derived from current local files and carries stale markers; memory is explicitly stored durable context with scope, type, status, provenance, lifecycle, and citations. Stage 07 introduces that local memory layer without adding Stage 08 observability polish or Stage 09 visual redesign.

## Goals / Non-Goals

**Goals:**

- Add a typed/scoped local memory record model with statuses, confidence, tags, source metadata, events, citations, tombstones, and shared schemas.
- Add manual memory CRUD and lifecycle APIs backed by Kira-owned SQLite storage.
- Add deterministic, explainable lexical retrieval with scope/type filters, top-k, dedupe, score reasons, and budget integration.
- Inject memories only through `ContextItem(kind="memory")`, with citations and run context trace visibility.
- Add post-run extraction dry-run that produces candidates but does not write automatically.
- Add deterministic fixture/mock extraction for tests and no-key local runs.
- Add secret/sensitive guard before all memory writes and candidate persistence.
- Add frontend memory inspector for list, search/explain, add/edit, candidate review, and lifecycle actions.

**Non-Goals:**

- No vector DB, embeddings, semantic search dependency, or hybrid ranking.
- No cloud/team memory sync, remote memory service, or shared multi-user permission model.
- No automatic writes to `project` or `user` scope without policy or HITL approval.
- No Stage 08 audit log, doctor checks, broad trace export, or remembered permission policy.
- No Stage 09 visual redesign or new design system.
- No general shell tool and no project file mutation tools.

## Decisions

### Decision: Store memory in Kira-owned SQLite

Memory records, citations, events, retrieval traces, extraction candidates, and tombstones SHALL live in the existing Kira-owned runtime database. This keeps Stage 07 local-first, testable with `KIRA_RUNTIME_DB_PATH`, and aligned with Stage 04/06 storage.

Alternatives considered:

- Store memory in project files: rejected because memory is local durable agent state and must not mutate project roots.
- Use a separate database: rejected because it increases operational surface before there is a multi-user or cloud memory requirement.

### Decision: Retrieval is lexical and explainable first

Memory retrieval SHALL start with deterministic lexical scoring: query overlap, scope match, type match, tags, confidence, recency, and previous usefulness. Each result carries score reasons and omission metadata.

Alternatives considered:

- Add embeddings immediately: rejected because Stage 07 needs trust, provenance, and lifecycle first.
- Use only creation time or manual pinning: rejected because memory must be searchable and explainable across workflows.

### Decision: ContextItems are the only provider injection path

Selected memory records SHALL become `ContextItem(kind="memory")` with citations before model input assembly. Provider requests receive memory through the existing context budget path, not through raw prompt concatenation.

Alternatives considered:

- Inject memory directly into prompts: rejected because it loses budget, citation, scope, and omission trace metadata.
- Store memory only for UI lookup: rejected because Stage 07 must make memory usable by runs.

### Decision: Extraction defaults to dry-run

Post-run extraction SHALL produce candidates with confidence, source, reason, risk, dedupe status, and suggested scope/type. Candidates are not written automatically by default.

Alternatives considered:

- Automatically write high-confidence memories: rejected until Stage 08 policy/audit hardening exists.
- Skip extraction entirely: rejected because users need a reviewable way to turn useful run outcomes into durable memory.

### Decision: Secret guard is mandatory before persistence

All memory record writes and extraction candidates SHALL pass a secret/sensitive guard before persistence. The guard blocks raw provider config, API keys, tokens, cookies, private keys, `.env` values, unredacted upstream errors, and high-risk personal/customer data patterns.

Alternatives considered:

- Rely on UI warnings: rejected because secrets can enter through API calls or extraction.
- Redact after persistence: rejected because raw secrets must never be stored.

### Decision: HITL approval reuses Stage 05 interrupts

Memory writes that require approval, such as `project`/`user` promotion or high-risk extracted candidates, SHALL reuse Stage 05 HITL semantics rather than introducing a parallel approval system.

Alternatives considered:

- Add a separate memory approval protocol: rejected because it duplicates interrupt/resume behavior.
- Block all non-session writes: rejected because project/user memories are part of the Stage 07 target, but writes must be inspectable.

## Risks / Trade-offs

- Wrong or temporary memories degrade later runs -> Default to manual writes, dry-run extraction, explicit lifecycle actions, and visible retrieval explanations.
- Secret patterns can be missed -> Use layered deny patterns, redaction tests, and never persist rejected candidate text.
- Retrieval may over-inject weak matches -> Require active status, scope filters, top-k limits, budget packing, and score reason visibility.
- Memory can overlap project knowledge -> Require source/type classification and avoid storing facts that are better derived from current project files.
- UI can hide why memory affected a run -> Show memory citations in run context traces and memory inspector explanations.

## Migration Plan

1. Add shared memory schemas and backend Pydantic models.
2. Add SQLite migrations for memory records, citations, events, tombstones, retrieval traces, and extraction candidates.
3. Implement memory repository, validation, secret guard, and manual CRUD APIs.
4. Implement retrieval scorer, dedupe, explanations, citations, and ContextItem conversion.
5. Integrate memory retrieval controls into run creation and context trace persistence.
6. Implement post-run extraction dry-run with fixture/mock extractor and optional real-provider path.
7. Implement lifecycle actions and policy/HITL approval hooks.
8. Add frontend memory inspector and run context memory citation display.
9. Add docs and regression tests across server, shared schemas, and frontend.

Rollback can leave memory tables unused while Stage 01-06 behavior continues. Existing run creation, provider selection, project retrieval, skills, HITL, and replay must keep working when memory retrieval is disabled.

## Open Questions

- Should `session` memory expire automatically by default, or only through explicit lifecycle actions?
- What exact threshold makes extracted memory high-risk enough to require HITL approval in Stage 07 before Stage 08 policy hardening?
- Should project-local memory default to the resolved project root ID from Stage 06 or allow a user-provided project label?
