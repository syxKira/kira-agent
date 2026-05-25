# Stage 07: Memory System

## Goal

Upgrade Kira from no/placeholder memory into a full local memory system modeled after Kai Stage 13: typed/scoped memory, explainable retrieval, post-run extraction candidates, citations, lifecycle operations, secret guard, and Web/API inspection.

## Why This Stage

Kai explicitly separates Memory v0 from the complete memory system. Kira should not stop at manual key-value notes because a general Web Agent needs durable preferences, workflow decisions, project facts, and failure lessons that are inspectable, scoped, removable, and safe. Memory must also stay distinct from Stage 06 project knowledge: files are current local evidence with citations and stale markers, while memory is durable learned context.

## Scope

- Memory scopes: `session`, `projectLocal`, `project`, `user`.
- Memory types: `preference`, `feedback`, `decision`, `project`, `reference`, `fact`, `workflow`.
- Memory status: `active`, `stale`, `archived`.
- Manual CRUD through API and frontend.
- Explainable retrieval with top-k, budget, dedupe, score reasons, and ContextItem injection.
- Memory citations whenever a memory is injected into model context.
- Post-run extraction dry-run that produces candidates, not automatic writes.
- Secret/sensitive guard before memory writes.
- Lifecycle actions: explain, archive, delete, merge, refresh, promote.
- Memory extraction and retrieval explain must work with mock/fixture providers in tests and real providers only when configured.

Excluded:

- Vector database.
- Cloud/team memory sync.
- Automatic writes to user/project scope without policy or HITL.
- Treating memory as transcript, skill, or project search.
- Solving ordinary multi-turn chat continuity through memory retrieval; Stage 08 owns transcript.

## Inputs And Dependencies

- Stage 04 session projection and checkpoints.
- Stage 05 HITL for memory approval.
- Stage 06 ContextItem builder, skill package contract, and project knowledge citations.
- Stage 09 permission/audit will harden policy and exports.
- Stage 08 transcript can feed extraction candidates, but does not change memory write policy.
- Real LLM provider contract for provider selection, fixture fallback, and redacted provider metadata.
- Kai Stage 13 memory model.
- Claude memory prefetch/extraction and memdir references.
- Codex memory citation/consolidation concepts.

## Design

### Memory Record

```python
class MemoryRecord(TypedDict, total=False):
    id: str
    scope: Literal["session", "projectLocal", "project", "user"]
    type: Literal["preference", "feedback", "decision", "project", "reference", "fact", "workflow"]
    status: Literal["active", "stale", "archived"]
    text: str
    tags: list[str]
    confidence: float
    source: dict
    created_at: str
    updated_at: str
    last_used_at: str | None
    expires_at: str | None
```

Memory is not the transcript and not the project index. It only stores durable facts, preferences, and decisions that remain useful across turns or sessions and cannot be reliably derived from current project files.

### Retrieval

Retrieval returns bounded ContextItems:

```python
class MemoryContextMetadata(TypedDict):
    memory_id: str
    scope: str
    type: str
    score: float
    citation_id: str
    source_summary: str
```

Scoring starts explainable: keyword overlap, scope match, type match, recency, confidence, and prior usefulness. Embeddings are deferred until there is evidence that explainable ranking is insufficient.

### Extraction

Post-run extraction:

1. Reads final transcript summary, user feedback, tool summaries, selected skill, and workflow outcome.
2. Skips extraction if the user already manually added memory in the run.
3. Produces `MemoryCandidate[]`.
4. Applies secret guard and dedupe.
5. Defaults to dry-run.
6. Uses the selected provider only when real model access is available; otherwise falls back to deterministic mock extraction for tests or skips extraction with an explainable status.
7. Writes only when policy allows low-risk project-local candidates or HITL approval is provided.

Memory records must never store provider `apiKey`, raw config files, request authorization headers, or unredacted provider errors. Provider profile IDs and model names may appear in source metadata only after redaction and only when useful for debugging memory provenance.

### Lifecycle

| Action | Behavior |
| --- | --- |
| explain | Show why a memory matched a query |
| archive | Keep but stop injecting |
| delete | Remove record and leave tombstone/audit marker |
| merge | Combine duplicates and preserve sources/citations |
| refresh | Update confidence/source after new evidence |
| promote | Move `projectLocal` to `project` or `user` after approval |
| stale | Mark expired/conflicting memory as non-injected |

## Implementation Tasks

1. Add SQLite memory tables for records, events, citations, and tombstones.
2. Implement Memory CRUD API and frontend memory inspector.
3. Implement retrieval scoring, top-k, budget, dedupe, and explain.
4. Inject active memories only through `ContextItem(kind="memory")`.
5. Record citations for injected memories.
6. Implement secret guard for keys, tokens, cookies, private keys, `.env` values, and high-risk personal/customer data.
7. Implement post-run extraction dry-run.
8. Add deterministic mock/fixture extraction path for tests and no-key local runs.
9. Add HITL approval for user/project scope writes and high-risk candidates.
10. Implement lifecycle operations.
11. Add replay/debug export showing which memories were injected and why.

## Validation

- Manual memory add/list/search/delete works through API.
- Retrieval order is deterministic for fixture queries and exposes score reasons.
- Stale/archived memories are not injected by default.
- Every injected memory creates a citation record.
- Extraction dry-run produces candidates without writing.
- Extraction tests do not require a real API key by default.
- Provider config, API keys, and unredacted upstream errors cannot be stored as memory.
- Secret guard blocks sensitive values.
- Merge/archive/delete/promote are covered by tests.
- Context injection uses budgeted ContextItems only.

## Exit Criteria

- Kira memory is typed, scoped, cited, explainable, and removable.
- Memory cannot silently store sensitive or temporary facts.
- The frontend can show why the agent remembered something.

## Deferred Work

- Vector/hybrid retrieval, team sync, and automatic high-confidence extraction can be evaluated after real trace data.
