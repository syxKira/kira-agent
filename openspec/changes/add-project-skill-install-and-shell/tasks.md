## 1. Skill Package Install And Metadata

- [x] 1.1 Extend skill frontmatter models and public metadata for invocation fields.
- [x] 1.2 Add safe zip installation service for project-local `.kira/skills`.
- [x] 1.3 Add `POST /api/skills/install` with redacted audit records.
- [x] 1.4 Add server tests for valid install, metadata filtering, and unsafe zip rejection.

## 2. Skill Activation And Routing

- [x] 2.1 Implement conservative prompt auto-routing against active skill catalog metadata.
- [x] 2.2 Split activated long `SKILL.md` bodies into ordered bounded context chunks with installation path hints.
- [x] 2.3 Add server tests for auto-route, disabled model invocation, and long doc chunking.

## 3. Controlled Shell Execution

- [x] 3.1 Add `run_shell_command` tool with project cwd validation, timeout, output caps, and redaction.
- [x] 3.2 Expose the shell tool to project-bound default agent runs and update the system prompt.
- [x] 3.3 Add permission/audit policy support for `shell.run`.
- [x] 3.4 Add server tests for shell success, cwd escape rejection, timeout, and tool metadata.

## 4. Web Project Root Integration

- [x] 4.1 Default the workbench project root to the current repo root via Vite env fallback.
- [x] 4.2 Refresh skills with the project root and include project root in normal run payloads.
- [x] 4.3 Add or update web tests for project skill catalog requests and run payload project root.

## 5. Roadmap And Validation

- [x] 5.1 Update relevant roadmap/stage docs to record skill install UX and controlled shell execution as intentional scope.
- [x] 5.2 Run focused server tests.
- [x] 5.3 Run focused web tests/typecheck if frontend changes require it.
- [x] 5.4 Validate `add-project-skill-install-and-shell` with OpenSpec strict mode.

## 6. Project Document Context

- [x] 6.1 Expose read-only project knowledge tools for on-demand retrieval when a run has a project root.
- [x] 6.2 Expand live lexical search from exact prompt text to bounded keyword queries for mixed Chinese/code prompts.
- [x] 6.3 Keep prompt-derived context injection as explicit opt-in rather than default behavior.
- [x] 6.4 Add server tests for default no-preload behavior and opt-in prompt retrieval.

## 7. Codex Parity Observations

- [x] 7.1 Compare local Codex skill execution against Kira fixture trace for the ad attribution prompt.
- [x] 7.2 Preserve activated skill documentation chunk order in packed context.
- [x] 7.3 Rewrite imported `.cursor` / `.codex` skill script examples to Kira's actual installed path before model injection.
- [x] 7.4 Instruct the default agent to stop after missing credential errors instead of probing `.env` or secret values.
- [x] 7.5 Reject shell commands that attempt to print `.env` files or secret environment variables.
- [x] 7.6 Keep run and tool-event skill metadata lightweight by excluding full `SKILL.md` bodies.
- [x] 7.7 Instruct the default agent not to mix fields or commands across unrelated skill templates.
- [x] 7.8 Instruct the default agent not to ask users to paste secrets into chat.
- [x] 7.9 Select prompt-relevant `SKILL.md` sections before injecting activated skill docs.
- [x] 7.10 Instruct the default agent to call send scripts directly with compact JSON instead of synthesizing JSON through shell pipelines.
- [x] 7.11 Keep selected skill field-constraint sections available and instruct the agent to satisfy those constraints literally.
- [x] 7.12 Disable further tool calls after missing credential shell failures so the agent reports the local config gap instead of probing secrets.
- [x] 7.13 Clarify shell tool schema and default prompt that compressed JSON means minified one-line JSON passed directly to the target script.
- [x] 7.14 Return a deterministic missing-credential message so user-visible replies do not ask for pasted tokens or repeat the JSON block.
- [x] 7.15 Internally reject preliminary JSON synthesis shell calls so the visible trace contains only the target send script call.
- [x] 7.16 Tighten the ad attribution skill rule that raw `ad_tracker.match_type` stays empty unless the user explicitly asks for an attributed result payload.
