## Why

Kira can discover skill packages that already exist on disk, but it cannot yet install user-provided zip packages or reliably use bundled skill instructions and scripts from a normal chat prompt. This blocks real local skill workflows such as ad attribution data generation, sending, and validation.

The execution boundary is also changing by explicit product direction: Kira should be able to run shell commands in a Codex-like local-agent workflow, while keeping local safety, redaction, timeouts, project-root boundaries, and auditability.

## What Changes

- Add project-local skill zip installation into `.kira/skills`.
- Filter macOS zip metadata and unsafe zip paths during installation.
- Extend skill metadata parsing for invocation hints such as `disable-model-invocation`, `user-invocable`, and `model-invocable`.
- Add simple backend auto-routing so matching prompts can activate a local skill without requiring the user to pick it manually.
- Load activated skill docs in bounded chunks so long `SKILL.md` files do not lose late sections such as send-script instructions.
- Add a controlled shell tool available to the default agent when a project root is bound.
- Pass project root from the frontend by default so project skills are visible in the normal chat.
- Preserve the default conversation-first UI while allowing slash skill selection.
- Update roadmap/docs to reflect the intentionally changed execution boundary.

## Capabilities

### New Capabilities

- `project-skill-installation`: Install local skill zip packages into the selected project and expose installation diagnostics.
- `controlled-shell-execution`: Run bounded shell commands from Kira with cwd, env, timeout, output limits, redaction, and audit metadata.

### Modified Capabilities

- `skill-package-contract`: Add installable zip package behavior, invocation metadata, and chunked activated skill context.
- `skill-workflow-discovery`: Add backend auto-routing from prompt to validated project/user skills.
- `tool-registry-schema`: Expose the new shell tool schema and risk metadata.
- `safety-permission-policy`: Add shell-run policy and audit requirements.
- `skill-and-project-ui`: Ensure the frontend uses the current project root for skill catalog and run creation.

## Impact

- Backend: skill package loader, skill install API, run creation routing, context packing, shell tool registry, permissions, audit.
- Frontend: default project root handling, skill refresh, run payloads.
- Shared contracts: skill install API payloads and shell tool schema through existing tool metadata.
- Docs/OpenSpec: Stage 06/09 boundary updates because skill installation and shell execution are now in scope.
- Tests: server tests for zip install, metadata parsing, auto-route, shell execution bounds; web tests for project-root run payload.
