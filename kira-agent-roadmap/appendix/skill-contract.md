# Appendix: Skill Contract

Kira skills combine Kai's ContextItem/progressive-loading approach, Claude's richer frontmatter and two-layer permission model, and Codex's concise package anatomy.

## Package Anatomy

```text
skill-name/
  SKILL.md                  # required
  skill.yaml                # required for workflow/tool skills
  workflows/
  tools/
  references/
  assets/
  fixtures/
  agents/
    openai.yaml             # optional UI metadata
```

## Required SKILL.md

`SKILL.md` is required for every skill. Its frontmatter must include:

```yaml
---
name: skill-name
description: Use this when ...
---
```

Optional frontmatter fields:

| Field | Purpose |
| --- | --- |
| `when_to_use` | Stronger routing guidance than description |
| `allowed-tools` | Human-readable allowed tool hint, normalized into manifest policy if present |
| `argument-hint` | UI/user hint for manual invocation |
| `model` | Optional model override |
| `effort` | Optional reasoning/effort hint |
| `context` | `main` or `fork`; fork-like behavior is future work |
| `disable-model-invocation` | Prevent model auto-calling this skill |
| `user-invocable` | Control whether it appears as a user-selectable skill |

The body is loaded only after activation.

## Optional skill.yaml

`skill.yaml` is required when the skill provides workflows, tools, permission policy, fixtures, or UI metadata beyond simple docs.

```yaml
id: example-skill
version: 0.1.0
display:
  name: Example Skill
  description: Run an example workflow.
invocation:
  user_invocable: true
  model_invocable: true
  auto_route: true
permissions:
  tools:
    allow:
      - read_project_file
  actions:
    ask:
      - external_send
workflows:
  - id: default
    entry: workflows/default.yaml
    reliability:
      timeout_seconds: 120
      retry:
        max_attempts: 1
      side_effects:
        require_idempotency_key: true
model:
  profile: minimax-global
  effort: medium
context:
  references:
    - references/overview.md
  project_files:
    globs:
      - "docs/**/*.md"
fixtures:
  - fixtures/basic.json
```

Workflow declarations can provide reliability hints, but core policy remains the upper bound. For example, a skill may reduce retry attempts or mark a node as non-idempotent; it cannot force Kira to retry an unsafe side effect.

Model hints are profile preferences, not provider configuration. A skill can request a configured profile ID or effort level, but it must not define `apiKey`, `baseURL`, authorization headers, or raw provider credentials.

Project file context hints are retrieval hints, not direct prompt injection. They constrain inventory/search candidates and still pass through Stage 06 citations, stale checks, prompt-injection labeling, and ContextItem budgeting.

## Validation Rules

- `name`/`id` must be stable and URL/path safe.
- Workflow skills must declare workflows and allowed tools.
- Skill permissions can narrow core policy but cannot expand it silently.
- Workflow reliability hints must include explicit side-effect/idempotency metadata for external actions.
- Model hints must reference configured profiles only and cannot carry secrets or custom base URLs.
- Project file hints must resolve inside the project root and obey ignore/sensitive-file policy.
- Remote/imported skills cannot execute inline shell.
- Python scripts must go through `run_python_script`.
- Full skill docs and references are loaded progressively.
- Every workflow skill must include at least one fixture.
