# Appendix: Project Knowledge Retrieval

## Purpose

Kira's local file access starts as three read-only tools, but a general web agent needs a retrieval system: inventory, indexing, chunking, ranking, citations, freshness checks, context packing, and prompt-injection boundaries. The system should make retrieved project content explainable and budgeted rather than dumping arbitrary grep output into the prompt.

## Boundaries

- The retrieval system never writes, moves, deletes, patches, formats, or stages project files.
- Its only writes are Kira-owned SQLite/cache records.
- All project file reads go through the same root, ignore, binary, large-file, and symlink escape policy as Stage 02 tools.
- Retrieved content is treated as untrusted project data, not as instructions.
- Results enter the model only as ContextItems with citations and token budgets.

## Components

| Component | Responsibility |
| --- | --- |
| `ProjectRootResolver` | resolve allowed roots and reject traversal/symlink escape |
| `ProjectInventory` | discover files, apply ignore policy, track mtime/size/hash/type |
| `ProjectChunker` | split readable files into stable chunks with line/byte ranges |
| `ProjectIndex` | store file/chunk metadata in SQLite; use FTS5 when available |
| `ProjectRetriever` | generate and rank candidates from `rg`, FTS, path filters, skill hints, and recency |
| `CitationBuilder` | produce path, line range, chunk ID, content hash, indexed-at, stale flag |
| `ContextPacker` | dedupe, truncate, and pack snippets into ContextItems |
| `ProjectKnowledgePanel` | show index status, retrieved snippets, citations, omitted results, and stale files |

## Data Model

| Entity | Key Fields |
| --- | --- |
| `project_roots` | root ID, canonical path hash, trust level, created_at |
| `project_files` | file ID, root ID, path, size, mtime, hash, type, ignored flag, reason |
| `project_chunks` | chunk ID, file ID, start/end byte, start/end line, hash, text preview |
| `project_fts` | chunk ID, indexed text for SQLite FTS |
| `project_retrievals` | query, filters, selected chunk IDs, omitted count, budget, timestamp |
| `project_citations` | ContextItem ID, file path, line range, chunk hash, stale flag |

Chunk IDs should be stable across unchanged content:

```text
root_id + relative_path + content_hash + start_line + end_line
```

## Retrieval Flow

1. Resolve root and permission policy.
2. Refresh inventory within time/file-count caps.
3. Detect changed/deleted files by mtime/size and confirm with hash when needed.
4. Generate candidates from live `rg`, SQLite FTS, active skill hints, explicit user paths, and recent conversation context.
5. Rank candidates by lexical score, path relevance, file type, freshness, recency, and user-selected scope.
6. Build snippets with citations and stale-source markers.
7. Label all snippets as project data.
8. Pack into ContextItems with truncation and omission metadata.
9. Persist retrieval trace for debug and replay.

## ContextItem Shape

```python
class ProjectContextMetadata(TypedDict):
    root_id: str
    path: str
    start_line: int | None
    end_line: int | None
    chunk_id: str | None
    content_hash: str | None
    indexed_at: str | None
    stale: bool
    retrieval_query: str | None
    omitted_count: int
    trust: Literal["project_data", "user_selected", "skill_reference"]
```

`trust="project_data"` means the model may use the content as evidence, but must not treat it as higher-priority instructions than system/developer/user messages.

## Search Strategy

v0 should prefer reliable lexical retrieval:

- live `rg` for fresh exact matches and no-index fallback;
- SQLite FTS5 for repeated local searches and UI exploration;
- path/type filters from skill manifests and user selection;
- no embedding dependency in the first local milestone.

Hybrid/vector retrieval is deferred until Kira has citation quality, staleness, injection handling, and evaluation fixtures.

## Prompt-Injection Controls

Local files can contain hostile or accidental instructions. Kira should:

- label retrieved snippets as untrusted project data;
- keep source text separated from system/developer instructions in provider input;
- preserve citations so answers can be grounded;
- avoid granting tool permissions based only on retrieved content;
- require HITL for high-risk actions suggested by retrieved text;
- include adversarial fixture files in tests.

## API Surface

| Endpoint | Responsibility |
| --- | --- |
| `GET /api/project/index` | root status, file count, chunk count, stale count, last refresh |
| `POST /api/project/index/refresh` | refresh inventory/index within caps |
| `GET /api/project/search` | search indexed/live project content with citations |
| `GET /api/project/files` | list files using inventory and Stage 02 rules |
| `GET /api/project/files/{path}` | read bounded file slice with citation metadata |
| `GET /api/runs/{thread_id}/context` | show project ContextItems included/omitted for a run |

These endpoints are local-debug APIs first. They should reuse the same policy and result shapes as tools so UI and model paths stay consistent.

## Evaluation Fixtures

| Fixture | What It Proves |
| --- | --- |
| ignored directories | `.git`, dependencies, caches, build outputs stay out |
| binary and large files | structured errors and no prompt injection |
| symlink escape | root boundary is enforced |
| modified file after index | stale flag appears and refresh updates citations |
| adversarial instructions in file | retrieved text is labeled as data and cannot grant permissions |
| no `rg` installed | Python fallback still produces bounded results |
| dense search result | ContextPacker truncates and records omitted count |

## Deferred

- Vector embeddings and hybrid semantic search.
- Cross-project knowledge base.
- OCR/PDF/DOCX parsing.
- Remote repositories or cloud indexes.
- Learned ranking.
