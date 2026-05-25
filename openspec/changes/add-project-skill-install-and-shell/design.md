## Context

Kira already has a local skill package reader, a project-root policy, a tool registry, and a default OpenAI-compatible agent loop. The current implementation stops short of three product behaviors needed by real skill packs:

- installing a zip into the selected project;
- routing a plain chat prompt to a matching project skill;
- executing the skill's bundled scripts from the local agent.

This change intentionally revises the previous Stage 06/09 execution boundary. Kira will expose shell execution as a controlled local tool, because the user wants Codex-like local command execution. The implementation keeps the Kira constraints that still matter for a browser-based local agent: project-root anchoring, bounded output, timeouts, redaction, and audit-friendly metadata.

## Goals / Non-Goals

**Goals:**

- Install local zip skill packages into `.kira/skills`.
- Discover those project skills in the normal browser chat without hidden debug panels.
- Route matching prompts to skill instructions automatically when confidence is clear.
- Preserve explicit slash skill selection.
- Load long activated skill docs in chunks so late instructions survive context packing.
- Add a `run_shell_command` tool that runs under a project-local cwd with bounded runtime and output.
- Keep secrets out of frontend output, provider context traces, and audit exports.

**Non-Goals:**

- Remote skill registry or signed marketplace.
- OS-level sandboxing.
- Rich dependency installation for skill packages.
- Full LangGraph workflow authoring for these ad attribution skills.
- Rewriting external scripts or hardcoding ad attribution business logic into Kira core.

## Decisions

### Install Zip Packages Project-Locally

Skill installs target `.kira/skills/<skill-id>` inside the selected project root. The installer reads the zip, rejects path traversal, skips macOS metadata and bytecode/cache folders, requires one top-level `SKILL.md`, and returns the parsed package metadata. This keeps project skills portable without writing outside the project tree.

Alternative considered: only document manual copy. That would not satisfy the product goal of installing user-provided zips from the local UI/API.

### Auto Route Before Loading Full Docs

Run creation will use catalog metadata to choose a project/user skill when the user does not explicitly select one. Routing remains lexical and conservative for the MVP: skill ID, name, description, and `when_to_use` are scored against the prompt. Explicit user selection always wins.

Alternative considered: ask the LLM to route skills. That would add latency and make routing depend on a real provider before skill context is available.

### Chunk Skill Docs After Activation

`skill_context_items` will split large `SKILL.md` bodies into named ContextItems. This avoids losing important late sections such as send-script instructions under the existing `max_item_chars` budget.

Alternative considered: increase the global context item size. That would risk bloating every run rather than fixing long skill docs.

### Add Controlled Shell Rather Than Script-Specific Wrappers

The execution layer follows the requested Codex-like direction: one shell tool can run commands. The shell tool still has structured arguments, bounded timeout/output, project-local cwd validation, sanitized environment overrides, and secret redaction. It does not use a general interactive terminal.

Alternative considered: typed wrappers per ad attribution script. That is safer but does not match the requested execution direction.

### Expose Shell To Project-Bound Agent Runs

The default agent loop will include `run_shell_command` when a project root is bound. This allows activated skill docs to instruct the model to run bundled scripts. The system prompt will identify shell as a local tool with bounded execution and remind the model to avoid secrets in visible output.

Alternative considered: expose shell only when a manifest declares it. The current ad attribution zip files have no `skill.yaml`, so that would keep the desired workflow blocked.

### Frontend Uses Current Project Root

The web app will default `project_root` to the repo root configured at build/runtime time, then pass it to skill catalog and run creation. This makes project-local `.kira/skills` visible without reintroducing the removed operator inspector.

## Risks / Trade-offs

- Shell can mutate files or call external services → Bound to project cwd by default, audited through tool events, redacted, timed out, and intentionally product-approved by this change.
- Long-running external DS workflows may exceed default limits → Raise shell timeout cap enough for local skill scripts while preserving a maximum.
- Auto-route may select the wrong skill → Use conservative lexical scoring, expose selected skill in run metadata, and allow slash selection/clear to override.
- Installed zips may contain metadata folders → Installer filters `__MACOSX`, `._*`, caches, and pyc files.
- Existing roadmap says no general shell → Update roadmap/stage docs in this patch to reflect the explicit boundary change.

## Migration Plan

Existing skills remain discoverable. Project installs add a new `.kira/skills` directory only when the user calls the install API. Existing conversations and run records are unaffected.

Rollback is straightforward: remove the shell tool from the registry/default agent allowlist and delete installed project skill directories. The install API does not modify source files outside `.kira/skills`.
