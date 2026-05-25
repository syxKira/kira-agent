# Appendix: Memory Model

Kira memory follows Kai Stage 13's model: typed, scoped, cited, explainable, conservative, and removable.

## Memory Is Not

- not transcript;
- not project search;
- not skill documentation;
- not a raw knowledge dump;
- not a place for secrets;
- not a substitute for current project files.

## Relation To Transcript

Transcript is the conversation-scoped ordered record of visible turns and bounded tool summaries. Memory is a curated durable record that may outlive a conversation. Stage 08 may feed completed transcript summaries into memory extraction, but Stage 07 write policy still decides whether anything becomes memory.

Do not use memory retrieval as the primary mechanism for ordinary follow-up questions. Follow-ups should first use `conversation_history` and `conversation_summary` ContextItems, then memory when a durable fact or preference is relevant.

## Scopes

| Scope | Meaning | Default write policy |
| --- | --- | --- |
| `session` | Useful only inside the current run/session | allow for explicit user action |
| `projectLocal` | Local private memory for one project checkout | allow for low-risk explicit user action |
| `project` | Shared project memory | ask |
| `user` | Cross-project user preference/fact memory | ask |

## Types

| Type | Examples |
| --- | --- |
| `preference` | User prefers concise summaries |
| `feedback` | User disliked a workflow behavior |
| `decision` | Approved design or implementation choice |
| `project` | Stable project-specific fact not better read from files |
| `reference` | Durable pointer to a useful local or external source |
| `fact` | Stable fact with provenance |
| `workflow` | Reusable lesson about skill/workflow execution |

## Required Fields

```python
MemoryRecord = {
    "id": str,
    "scope": str,
    "type": str,
    "status": str,
    "text": str,
    "tags": list[str],
    "confidence": float,
    "source": dict,
    "created_at": str,
    "updated_at": str,
}
```

## Injection Rules

- Only `active` memories are injected by default.
- Retrieval must be bounded by top-k and token budget.
- Every injected memory creates a citation.
- Context uses `ContextItem(kind="memory")`.
- Debug output must explain score and cut reasons.

## Write Rules

- Manual writes are preferred early.
- Automatic extraction defaults to dry-run.
- User/project scope writes require policy or HITL approval.
- Secret guard runs before all writes.
- Extracted candidates must include source, reason, confidence, and risk.

## Lifecycle

| Action | Result |
| --- | --- |
| `archive` | Hide from injection without deleting |
| `delete` | Remove and record tombstone/audit marker |
| `merge` | Combine duplicate memories and preserve sources |
| `refresh` | Update confidence/source after new evidence |
| `promote` | Move memory to broader scope with approval |
| `stale` | Mark expired/conflicting memory as non-injected |
