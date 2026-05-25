## Context

Kira has reached the point where provider streaming, tools, skill graphs, durability, replay, and HITL exist. The next limitation is context quality: skills are still simple in-process metadata, and project context is still exposed mostly as direct file tools. Stage 06 creates two foundations that later stages depend on:

- a real local skill package contract that workflow authors can use without adding business logic to Kira core;
- a project knowledge retrieval system that turns local files into cited, budgeted, and stale-aware ContextItems.

This stage must preserve existing safety boundaries. Project files remain read-only. Skill model hints can influence provider selection but never carry secrets. Retrieved project content is data, not instructions. Memory stays out of scope until Stage 07.

## Goals / Non-Goals

**Goals:**

- Define package anatomy for local skills: required `SKILL.md`, optional `skill.yaml`, workflows, tools, references, assets, fixtures, and UI metadata.
- Discover skills from multiple local directories with duplicate/priority resolution and progressive loading.
- Validate skill manifests, permissions, workflow declarations/factories, fixtures, references, model hints, and context hints.
- Add ContextItem schemas and a budget builder for skill/project context with truncation and omission traces.
- Add project inventory, chunking, SQLite metadata/FTS indexing, lexical retrieval, citations, stale markers, and prompt-injection labeling.
- Add API and frontend surfaces to inspect skill packages, project index/search results, citations, omissions, and run context traces.

**Non-Goals:**

- No Stage 07 memory store, memory retrieval, extraction, or memory UI.
- No Stage 08 install/packaging polish, remote auth, broad audit UI, or remembered permission policy.
- No remote skill marketplace, signed package distribution, or skill install/update UX.
- No vector embeddings or semantic search dependency.
- No general shell tool or project file mutation tool.

## Decisions

### Decision: Keep `SKILL.md` as the progressive-loading entrypoint

`SKILL.md` is required for all skills. Catalog discovery reads only frontmatter plus a short summary. Full body and references load only after explicit activation, validated auto routing, or workflow-owned context needs.

Alternatives considered:

- Load all skill docs at startup: rejected because it violates ContextItem budgeting and makes auto routing expensive/noisy.
- Use only `skill.yaml`: rejected because skills need human/model-readable instructions that are progressively loaded.

### Decision: Use `skill.yaml` for machine-readable workflow/package metadata

`skill.yaml` is optional for simple instruction-only skills, but required when a skill declares workflows, tools, permissions, fixtures, UI metadata, or package context. This keeps simple skills lightweight while making workflow skills inspectable.

Alternatives considered:

- Put all machine metadata in frontmatter: rejected because workflow/tool/context metadata becomes too large and brittle.
- Require Python packages for every skill: rejected because Stage 06 is local-first and should support simple file packages.

### Decision: Lexical retrieval first, embeddings later

Project retrieval SHALL combine safe inventory, live `rg` candidates, and SQLite FTS when available. Embeddings and hybrid semantic ranking are deferred until citation quality and stale-source behavior are reliable.

Alternatives considered:

- Add vector search immediately: rejected because it adds dependency and evaluation complexity before trust/citation basics are stable.
- Use only live `rg`: rejected because repeated UI search and run context packing need indexed metadata, citations, and stale flags.

### Decision: ContextItems are the only model context boundary

Skill docs, skill references, workflow hints, project snippets, omissions, and permissions SHALL be represented as bounded ContextItems before model injection. Provider input assembly consumes ContextItems rather than raw file/skill payloads.

Alternatives considered:

- Inject retrieved text directly into prompts: rejected because it cannot carry budget, citation, stale, trust, or omission metadata.
- Keep context debug only in backend logs: rejected because the frontend needs to explain why a snippet was used.

### Decision: Skill permissions narrow core policy

Skill permissions can restrict which core tools/actions/model hints are available to a skill, but cannot silently expand beyond Kira core/project policy. Python execution remains controlled Python execution; no skill may add a general shell path.

Alternatives considered:

- Let skill manifests define arbitrary tool permissions: rejected because imported/local packages could escalate capabilities.
- Forbid skill-provided tools entirely: rejected because the package contract needs an extension point, but extension must be validated and bounded.

## Risks / Trade-offs

- Stage breadth -> Split implementation into package contract, ContextItems, project index, retrieval, API, and UI slices with independent tests.
- Large repository indexing latency -> Use file count/time caps, incremental refresh, ignore policy, and live `rg` fallback.
- Prompt injection through local files -> Label retrieved content as untrusted project data and never grant permissions from retrieved text.
- Skill routing overreach -> Require confidence thresholds and keep full doc loading behind explicit activation or validated route.
- Provider secret leakage through skill model hints -> Allow only configured profile/model/effort references and test redaction across API, traces, and UI.

## Migration Plan

1. Add shared schemas and backend models for skill packages, ContextItems, project index records, citations, retrieval results, and run context traces.
2. Introduce local skill package discovery alongside existing built-in skills, preserving current built-in fixture/test skills.
3. Add manifest validation, duplicate resolution, progressive loading, and skill detail APIs.
4. Add ContextItem builder and budget traces, then route skill context through it.
5. Add project inventory/chunk/index tables and safe incremental refresh.
6. Add lexical retrieval, citation builder, stale markers, and project ContextItems.
7. Add frontend skill/project panels and focused tests.
8. Update docs and run backend/frontend/OpenSpec validation.

Rollback can disable package/project discovery while keeping archived Stage 01-05 behavior. Existing direct provider, fixture, HITL, and built-in skill paths must continue working during the migration.

## Open Questions

- Which local skill directories should be enabled by default beyond bundled repo skills and user-local `~/.kira-agent/skills`?
- Should project indexing refresh automatically on every run with caps, or only on explicit refresh plus stale markers?
- How much of workflow factory execution should Stage 06 allow before Stage 08 hardens package permissions?
