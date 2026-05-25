## 1. Shared Contracts And Storage

- [x] 1.1 Add shared schema definitions for skill package metadata, `SKILL.md` frontmatter, `skill.yaml`, workflow hints, tool declarations, permission declarations, model hints, and validation diagnostics.
- [x] 1.2 Add shared schema definitions for typed `ContextItem` records, context budgets, packed context traces, truncation records, omission records, and citation references.
- [x] 1.3 Add shared schema definitions for project inventory entries, project chunks, retrieval results, stale result flags, and index status responses.
- [x] 1.4 Export TypeScript types for all new shared schemas from `src/` so `server/` and `web/` use the same contract names.
- [x] 1.5 Add backend persistence tables or migration helpers for skill discovery cache, project inventory, project chunks, retrieval metadata, and run context traces.
- [x] 1.6 Add contract tests that validate representative skill package, context item, project index, retrieval, and run context payloads against the shared schemas.

## 2. Skill Package Discovery And Validation

- [x] 2.1 Create backend skill package modules for discovery roots, package scanning, parsed package records, validation results, and package priority ordering.
- [x] 2.2 Implement default skill discovery roots for built-in skills and local user/project skills without requiring committed secrets or project-root API keys.
- [x] 2.3 Implement `SKILL.md` discovery with optional YAML frontmatter while preserving progressive-loading markdown behavior.
- [x] 2.4 Implement optional `skill.yaml` parsing for workflows, tool requirements, context files, permissions, fixtures, and model hints.
- [x] 2.5 Validate package manifests and report structured diagnostics for missing `SKILL.md`, invalid YAML, invalid workflow names, invalid permissions, invalid model hints, and unsupported tool declarations.
- [x] 2.6 Implement duplicate skill ID handling with deterministic priority rules and diagnostics for shadowed packages.
- [x] 2.7 Ensure package discovery loads only lightweight metadata by default and reads detailed skill content only on explicit detail or activation requests.
- [x] 2.8 Preserve compatibility with existing Stage 03 skill workflow discovery responses while enriching them with package metadata.
- [x] 2.9 Add backend tests for valid packages, malformed packages, duplicate IDs, progressive loading, priority ordering, and built-in skill compatibility.

## 3. Skill Activation, Permissions, And Model Hints

- [x] 3.1 Implement explicit skill activation controls for a run without requiring automatic execution of all discovered skills.
- [x] 3.2 Implement bounded auto-routing support that uses only lightweight skill summaries unless a skill is selected or activated.
- [x] 3.3 Resolve effective skill permissions from package metadata and expose them as redacted run metadata.
- [x] 3.4 Validate workflow entrypoint references before constructing a skill-backed LangGraph run.
- [x] 3.5 Load skill workflow factories only after validation and only for activated or selected skills.
- [x] 3.6 Convert selected skill instructions, declared context files, and fixture hints into typed `ContextItem` records for the provider input.
- [x] 3.7 Apply validated skill model hints to provider selection after per-request overrides and before configured defaults.
- [x] 3.8 Reject model hints that attempt to include secrets, raw API keys, unknown providers, or unsupported provider configuration fields.
- [x] 3.9 Add tests for explicit activation, bounded auto-routing, permission metadata, invalid workflow rejection, model hint precedence, and secret rejection.

## 4. Project Inventory And Index

- [x] 4.1 Create backend project knowledge modules for root policy resolution, inventory scanning, ignore handling, file classification, chunking, and index persistence.
- [x] 4.2 Reuse Stage 02 project-local read policy for all project inventory and file reads, including symlink containment checks.
- [x] 4.3 Implement capped inventory refresh with limits for file count, file size, binary detection, ignored directories, and total indexed bytes.
- [x] 4.4 Implement stable chunk IDs that include project-relative path, content position, content hash, and index version.
- [x] 4.5 Store indexed project chunks in Kira-owned SQLite storage rather than writing generated files into the project tree.
- [x] 4.6 Add SQLite FTS indexing when available and a deterministic lexical fallback when FTS is unavailable.
- [x] 4.7 Track index freshness using file metadata and content hashes so stale retrieval results can be marked.
- [x] 4.8 Add backend tests for ignored files, binary files, oversized files, symlinks outside the project, deleted files, modified files, and FTS fallback behavior.

## 5. Retrieval, Citations, And Context Packing

- [x] 5.1 Implement lexical project retrieval that can combine live file search candidates with indexed chunk candidates.
- [x] 5.2 Rank retrieval results deterministically using query term matches, path relevance, skill-declared context hints, and freshness state.
- [x] 5.3 Build citation records with project-relative path, line range or chunk range, content hash, and stale flag.
- [x] 5.4 Convert retrieval results into typed project `ContextItem` records labeled as untrusted project data.
- [x] 5.5 Implement a deterministic context budget packer that orders system, skill, project, run, and user items by policy.
- [x] 5.6 Record truncation and omission metadata whenever context items exceed budget limits.
- [x] 5.7 Persist the packed context trace for each run without storing secrets or raw provider credentials.
- [x] 5.8 Ensure prompt-injection-like project text remains labeled as project data and cannot become system or developer instructions.
- [x] 5.9 Add tests for retrieval ranking, citations, stale flags, context ordering, budget truncation, omission reporting, and project prompt-injection fixtures.

## 6. Backend APIs And Run Integration

- [x] 6.1 Extend skill list and detail APIs to expose package metadata, validation diagnostics, permissions, fixtures, workflow summaries, and optional detailed markdown content.
- [x] 6.2 Add or extend run creation APIs so callers can provide selected skill IDs, disabled skill IDs, project context controls, context budget controls, and provider/model overrides.
- [x] 6.3 Add project index status and refresh APIs that report indexed files, skipped files, last refresh time, freshness state, and validation errors.
- [x] 6.4 Add read-only project search and file citation APIs that return redacted retrieval results with project-relative paths only.
- [x] 6.5 Add run context trace API for inspecting selected skills, selected project context, citations, truncations, omissions, and provider selection metadata.
- [x] 6.6 Integrate packed context items into the existing real provider and fixture provider request flow without changing provider streaming semantics.
- [x] 6.7 Ensure fixture runs can execute deterministically with selected skills and project context disabled or supplied from fixtures.
- [x] 6.8 Add API tests for skill metadata, skill detail loading, project index status, project search, run context trace, provider integration, redaction, and fixture determinism.

## 7. Frontend Skill And Project UI

- [x] 7.1 Add a skill panel that lists discovered skills with name, summary, package source, validation status, permissions, and activation state.
- [x] 7.2 Add skill detail UI that loads full `SKILL.md` content only on demand and shows workflow/tool/context metadata without exposing secrets.
- [x] 7.3 Add run controls for selecting skills, disabling skills, choosing auto-routing behavior, and setting context budget options.
- [x] 7.4 Add a project knowledge panel that shows index status, refresh state, skipped file counts, stale state, and refresh action feedback.
- [x] 7.5 Add project search UI that displays retrieval snippets, citations, stale flags, and omitted/truncated result indicators.
- [x] 7.6 Add run context inspector UI showing selected skills, project citations, context item ordering, truncations, omissions, and provider selection metadata.
- [x] 7.7 Preserve the existing default real-LLM run behavior and fixture run button behavior from the archived frontend change.
- [x] 7.8 Add frontend tests for skill list/detail rendering, activation controls, project index panel, search results, context inspector, and no-secret rendering.

## 8. Fixtures, Regression, And Security Checks

- [x] 8.1 Add fixture skill packages covering simple instructions, workflow metadata, context files, permissions, invalid manifests, and duplicate IDs.
- [x] 8.2 Add fixture projects covering small repositories, ignored files, binary files, oversized files, stale chunks, and prompt-injection-like content.
- [x] 8.3 Verify project knowledge APIs and skill package discovery never mutate project files or write generated files into the project root.
- [x] 8.4 Verify raw API keys are absent from skill manifests, run state, graph checkpoints, provider metadata, logs, diagnostics, API responses, and frontend readiness state.
- [x] 8.5 Run Stage 01 local web loop regression tests for health, run creation, event streaming, and frontend boot.
- [x] 8.6 Run Stage 02 tool protocol regression tests for read-only file policy and controlled Python execution boundaries.
- [x] 8.7 Run Stage 03 skill graph regression tests for workflow discovery, graph construction, event mapping, and fixture runs.
- [x] 8.8 Run Stage 04 replay/checkpoint regression tests for checkpoint continuity, replay event consistency, and redacted persisted state.
- [x] 8.9 Run Stage 05 HITL regression tests for interrupt, approval, denial, edit, timeout, and resumed execution behavior.

## 9. Documentation And Validation

- [x] 9.1 Document skill package structure, `SKILL.md` frontmatter, `skill.yaml`, permissions, fixtures, and model hint rules in project docs.
- [x] 9.2 Document project knowledge indexing, retrieval limits, citations, staleness, context budgets, and prompt-injection handling.
- [x] 9.3 Document local configuration and runtime notes for using Stage 06 with fixture provider and real OpenAI-compatible providers.
- [x] 9.4 Run backend unit and integration tests for `server/`.
- [x] 9.5 Run shared schema/type validation for `src/`.
- [x] 9.6 Run frontend typecheck and tests for `web/`.
- [x] 9.7 Run `openspec validate "stage-06-skill-package-project-knowledge" --strict`.
- [x] 9.8 Run `openspec status --change "stage-06-skill-package-project-knowledge"` and confirm the change is ready for apply.
