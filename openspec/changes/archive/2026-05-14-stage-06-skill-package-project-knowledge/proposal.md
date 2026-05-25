## Why

Kira can now run local web conversations, tools, skill graphs, durable replay, and HITL, but skills are still loose in-process metadata and project context is still ad hoc file listing/search/reading. Stage 06 turns skills into inspectable packages and turns project files into cited, bounded ContextItems so real workflows can use local knowledge without hardcoding business logic into core.

## What Changes

- Add a stable local skill package contract built around required `SKILL.md` frontmatter and optional `skill.yaml` manifests.
- Support multi-directory skill discovery, duplicate/priority resolution, progressive loading, summary/detail APIs, explicit activation, and safe auto routing.
- Validate skill-provided workflow declarations/factories, tool permissions, UI metadata, fixtures, references, and model hints.
- Add a ContextItem contract and budget builder for skill catalog entries, activated skill docs, references, workflow hints, permissions, project snippets, omissions, and debug traces.
- Add a project knowledge retrieval layer: inventory, chunking, SQLite metadata/FTS index, live `rg` fallback, ranking, citations, stale-source detection, and prompt-injection labeling.
- Add local project knowledge APIs and frontend panels for skill catalog/details and project index/search/citations.
- Preserve Stage 02 read-only file boundaries and Stage 05 HITL; project index writes go only to Kira-owned SQLite/cache storage.
- Keep Stage 06 focused: no memory system, no remote marketplace, no arbitrary shell, and no project file mutation tools.

## Capabilities

### New Capabilities

- `skill-package-contract`: Defines `SKILL.md` frontmatter, optional `skill.yaml`, package anatomy, validation, progressive loading, duplicate/priority rules, fixtures, permissions, workflow declarations/factories, and frontend-safe skill details.
- `context-item-budgeting`: Defines bounded ContextItem shapes, token/budget packing, truncation/omission metadata, prompt-injection labeling, and context debug traces.
- `project-knowledge-index`: Defines project inventory, safe incremental refresh, chunking, SQLite metadata/FTS storage, stale-source detection, and read-only project index boundaries.
- `project-knowledge-retrieval`: Defines live/indexed lexical retrieval, citation building, ranking, cited ContextItems, APIs, and frontend project knowledge inspection.
- `skill-and-project-ui`: Defines frontend skill catalog/detail panel and project knowledge panel behavior for index status, search results, citations, stale files, omissions, permissions, workflows, model hints, and fixtures.

### Modified Capabilities

- `skill-workflow-discovery`: Upgrades minimal built-in workflow metadata into package-backed skill discovery and activation.
- `project-file-tools`: Requires project knowledge indexing/retrieval to reuse Stage 02 root, ignore, binary, large-file, and read-only file policies.
- `llm-provider-selection`: Adds validated skill model hints as provider selection inputs after request overrides and before configured defaults.
- `local-run-api`: Adds project/skill context controls and context inspection endpoints for runs.

## Impact

- Backend: skill registry/loading, manifest validation, workflow factory/declaration loading, project inventory/index/retrieval modules, ContextItem builder, run context assembly, and new project/context APIs.
- Frontend: skill catalog/detail UI, project knowledge/index/search UI, context/debug surfaces, and activation controls.
- Storage: SQLite tables for skill catalog cache, validation results, project roots/files/chunks/FTS/retrieval traces/citations/context traces.
- Shared contracts: schemas for skill packages, ContextItems, project index status, citations, retrieval results, and run context traces.
- Tests: package fixtures, duplicate resolution, progressive loading, provider hint validation/redaction, project policy reuse, chunking/indexing/FTS fallback, citations/stale markers, prompt-injection labeling, UI rendering, and no project mutation regression.

## Scope

- Local skill package discovery and validation only.
- Local project knowledge indexing and lexical retrieval only.
- ContextItem injection for skill/project context into provider input and debug traces.
- UI surfaces for inspecting skills and project knowledge.
- Deterministic fixtures that run without a real API key by default.

## Non-goals

- No Stage 07 memory records, memory extraction, memory retrieval, or memory lifecycle UI.
- No Stage 08 packaging polish, broad audit UI, diagnostics doctor, or remembered permissions policy.
- No remote skill registry, marketplace, signed package distribution, or install/update UX.
- No embedding/vector retrieval in this stage.
- No arbitrary shell tool and no project file write/edit/delete/patch/stage tools.
- No business-specific workflow hardcoded into Kira core.

## Acceptance Criteria

- A `SKILL.md`-only local skill appears in the catalog from summary metadata without loading its full body.
- A workflow skill with `skill.yaml` validates, exposes workflows/permissions/fixtures, and can be explicitly activated.
- Duplicate skills resolve by source/priority while shadowed skills remain inspectable.
- Skill model hints can affect provider selection only through configured provider profiles and are redacted in all public/debug payloads.
- Project inventory respects root boundaries, ignore rules, symlink escape, binary files, large-file caps, and read-only policy.
- Retrieval returns cited snippets with paths, line ranges, chunk IDs, content hashes, indexed-at timestamps, stale markers, and omission metadata.
- Retrieved project content is labeled as untrusted project data before provider injection.
- Context traces show included, truncated, and omitted skill/project ContextItems for a run.
- Frontend skill and project panels render catalog/details, permissions, workflows, index status, search results, citations, stale files, and omitted context.

## Risks

- Stage 06 is broad; implementation should keep independently testable slices for skill packages and project retrieval.
- Auto routing can over-load skill docs too early; progressive loading must be enforced by tests.
- Project indexing can become slow on large repos; inventory refresh must use caps and incremental checks.
- Retrieved local files can contain hostile instructions; ContextItems must label them as data and never expand permissions based on retrieved content.
