# Stage 06: Skill Package Contract + Project Knowledge

## Goal

Upgrade Kira skills from loose workflow metadata into a complete package contract, and upgrade local file access from primitive read/search tools into a project knowledge retrieval system. Skills can provide docs, tool definitions, workflow declarations or factories, context injection rules, UI metadata, permission hints, fixtures, and bundled resources. Project files can be inventoried, chunked, searched, cited, and packed into the model budget. All skill and project context still enters the model through ContextItems and the budget builder.

## Why This Stage

Kai Stage 10 already defines the important foundation: multi-directory discovery, `SKILL.md`, frontmatter scan, catalog injection, explicit slash activation, auto routing, duplicate/priority rules, and progressive loading. Kira needs those pieces, but because workflows are skill-driven, Kira also needs a stronger package contract before skill authors start defining LangGraph workflows.

The same is true for local files. A general agent needs more than `grep`: it needs a retrieval layer that can say which files were considered, why a snippet was selected, whether it is stale, how much prompt budget it consumes, and whether retrieved text should be treated as untrusted data rather than instructions.

## Scope

- Multi-directory skill discovery and duplicate/priority resolution.
- Required `SKILL.md` with concise frontmatter and progressive loading.
- Optional `skill.yaml` manifest for workflow/tool/context/UI/test metadata.
- Skill catalog API and frontend skill list.
- Explicit activation from UI and API metadata.
- Auto routing based on description, `when_to_use`, project context, and active workflow.
- Workflow declarations/factories owned by skills, not core.
- Tool permission declarations for skill-provided and core tools.
- Skill model hints that can request a model profile but cannot supply provider secrets.
- ContextItem injection for skill catalog, activated skill docs, references, and workflow hints.
- Project knowledge inventory and incremental index over allowed local files.
- File chunking with stable chunk IDs, source maps, line ranges, and content hashes.
- Lexical retrieval using live `rg` plus SQLite FTS index where available.
- Citation packing into `ContextItem(kind="project_file")` and `ContextItem(kind="project_search")`.
- Stale-source detection when files change after indexing.
- Prompt-injection labeling for retrieved local content.
- Skill fixtures for package validation and regression.

Excluded:

- Full memory system; Stage 07 owns memory.
- Remote skill marketplace.
- Remote skill installation/update UX beyond local project zip installation.
- Unbounded shell execution from skills.

## Inputs And Dependencies

- Stage 02 `BaseTool` registry.
- Stage 03 minimal workflow-capable skill loading.
- Stage 04 storage for catalog cache and validation output.
- Stage 05 HITL for permission-sensitive skill activation.
- Kai Stage 10 skill design.
- Claude-style rich skill frontmatter and fork/context concepts.
- Codex-style concise skill anatomy and bundled resources.
- Stage 02 read-only file tools and project root policy.
- Stage 04 storage and event/audit tables.
- Real LLM provider selection contract: request override, skill hint, configured default, then fixture fallback.

## Design

### Package Shape

```text
skill-name/
  SKILL.md                  # required human/model instructions
  skill.yaml                # optional machine-readable Kira manifest
  workflows/
    default.yaml            # optional declarative StateGraph workflow
    factory.py              # optional Python workflow factory
  tools/
    *.py                    # optional BaseTool providers
  references/
    *.md
  assets/
  fixtures/
    *.json
  agents/
    openai.yaml             # optional UI metadata for skill chips/lists
```

`SKILL.md` remains the progressive-loading entry point. Kira only reads frontmatter and a short description for the catalog. Full body and references load only after explicit activation or a validated auto-route.

### Manifest Contract

`skill.yaml` is optional in simple skills but required for workflow skills. The manifest is intentionally machine-readable so the web app can show capabilities before loading the full instructions.

```yaml
id: crowd-insight
version: 0.1.0
display:
  name: Crowd Insight
  description: Generate and inspect crowd analysis workflows.
invocation:
  user_invocable: true
  model_invocable: true
  auto_route: true
permissions:
  tools:
    allow:
      - read_project_file
      - search_project_files
      - run_python_script
  actions:
    ask:
      - external_send
workflows:
  - id: default
    entry: workflows/default.yaml
model:
  profile: minimax-global
  effort: medium
context:
  references:
    - references/overview.md
  project_files:
    globs:
      - "**/*.md"
fixtures:
  - fixtures/basic-run.json
```

### Activation And Context

Kira supports three activation modes:

| Mode | Source | Behavior |
| --- | --- | --- |
| explicit | user selects skill or API request names it | Always preferred if permission allows |
| auto | router matches task to skill metadata | Requires confidence threshold and may ask if risky |
| workflow | active workflow references its owning skill | Loads workflow context needed for current node |

Activated skills produce bounded ContextItems:

- `skill_catalog`: short metadata for available skills;
- `skill_doc`: loaded `SKILL.md` body;
- `skill_reference`: selected reference snippets;
- `workflow`: graph/node hints needed for execution;
- `model_hint`: optional profile/model preference for the run, after policy validation;
- `permission`: skill tool/action constraints.

Skill model hints participate in provider selection but never carry secrets. A skill may request a profile ID, model family, or effort hint, but it must not define `apiKey`, `baseURL`, or raw provider credentials. The run-level selection order remains:

1. explicit run request provider/model override;
2. validated skill model hint;
3. configured default provider/model;
4. fixture fallback when no valid API key is available and fallback is permitted.

### Project Knowledge Retrieval

Stage 02 file tools remain available for direct tool calls, but Stage 06 adds a retrieval system around them:

| Component | Responsibility |
| --- | --- |
| `ProjectInventory` | discover allowed files, apply ignore policy, store path/size/mtime/hash metadata |
| `ProjectChunker` | split text into stable chunks with path, byte range, line range, language/type hints |
| `ProjectIndex` | store file metadata and chunks in SQLite; use FTS5 when available |
| `ProjectRetriever` | combine live `rg` candidates, indexed matches, recency, path filters, and skill hints |
| `CitationBuilder` | attach source path, line range, chunk hash, indexed-at time, and stale flag |
| `ContextPacker` | dedupe snippets, respect token budget, and emit ContextItems |

Retrieval is intentionally source-grounded before it is semantic. v0 should prefer lexical `rg`/FTS, clear citations, and reliable freshness over embedding-based search. Embeddings or hybrid ranking can be added later after the trust and citation model is stable.

Project retrieval query flow:

1. Resolve project root and permission policy.
2. Choose an explicit `project_context_query` when provided; otherwise expose search/read tools and let the model retrieve project documents on demand. Prompt-derived preloading is available only through explicit `auto_project_context` opt-in.
3. Refresh inventory for changed files within time and file-count caps.
4. Generate candidates from live `rg`, indexed FTS, active skill hints, recent run context, and bounded keyword queries derived from longer natural-language prompts.
5. Rank by textual match, path relevance, file type, freshness, and user-selected scope.
6. Build cited snippets with line ranges and chunk hashes.
7. Label retrieved content as untrusted project data before model injection.
8. Pack results into ContextItems with truncation and omission metadata.

The retrieval system does not mutate project files. Its only writes are Kira-owned SQLite/cache records under Kira's local data directory.

### Permission Layers

Following Claude's two-level model, Kira separates:

1. Whether the skill may be invoked.
2. Which tools/actions the skill may use after invocation.

Skill permissions can narrow core tools but cannot silently expand beyond system/project policy. Project-local skills may use controlled shell execution when the run is bound to a project root and the Stage 09 policy allows it. Remote or imported skills must not bypass controlled execution. Python scripts from skills go through `run_python_script` or project-root controlled shell and the Stage 09 policy.

## Implementation Tasks

1. Define `SKILL.md` frontmatter schema: `name`, `description`, `when_to_use`, `argument_hint`, `model`, `effort`, `context`, `disable_model_invocation`, `user_invocable`.
2. Define optional `skill.yaml` schema for workflows, tools, context, permissions, UI metadata, fixtures, and dependencies.
3. Implement skill discovery directories and duplicate/priority rules adapted from Kai Stage 10.
4. Implement catalog cache and `GET /api/skills` detail modes: summary, manifest, activated context.
5. Implement progressive loader for `SKILL.md`, references, and assets.
6. Implement workflow validation for declarative graphs and Python factories.
7. Implement skill permission resolver: invocation permission plus tool/action/model-hint permission.
8. Implement model hint validation against configured provider profiles without exposing API keys.
9. Implement project inventory and incremental refresh over allowed files.
10. Implement chunking, source maps, SQLite metadata tables, and optional FTS5 index.
11. Implement retrieval ranking and citation builder.
12. Integrate project retrieval output with ContextItem budgeting and debug traces.
13. Implement fixture runner for skill packages, including fixture-provider runs when no real key is configured.
14. Add frontend skill panel showing status, source, permissions, workflows, model hints, and fixtures.
15. Add project knowledge panel showing index status, search results, citations, stale files, and omitted context.

## Validation

- A simple `SKILL.md`-only skill appears in the catalog without loading full body.
- A workflow skill with `skill.yaml` validates and exposes its workflows.
- Duplicate skills resolve by priority and source; shadowed skills remain inspectable.
- Explicit activation loads full body and selected references as ContextItems.
- Auto routing never loads full docs before a route is chosen.
- Skill tool/action permissions are enforced.
- Skill model hints can influence provider selection only through configured profile IDs and are redacted in UI/debug output.
- Skill fixture tests can run without hardcoded business workflow names.
- Project inventory respects ignore rules, path boundaries, binary/large-file exclusions, and symlink escape checks.
- Retrieval returns cited snippets with line ranges, chunk IDs, and stale-source markers.
- Context budget traces show included, truncated, and omitted project snippets.
- Retrieved project text is labeled as untrusted content before model injection.

## Exit Criteria

- Kira has a stable skill package contract suitable for workflow authors.
- Skill metadata, workflow capabilities, permissions, UI display, and fixtures are inspectable through API and frontend.
- Kira has a project knowledge retrieval system, not just ad hoc grep/read tools.
- Project snippets can be traced from model context back to source files and line ranges.
- Core still contains no business workflow node names.

## Deferred Work

- Remote registry, signed skill packages, and marketplace UX are future work; local zip installation is supported separately.
- Team policy distribution is deferred.
- Memory integration lands in Stage 07.
