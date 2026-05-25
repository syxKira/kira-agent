# Stage 09: Safety + Observability + Polish

## Goal

Harden Kira for regular local use: provider config safety, file access boundaries, project retrieval safety, graph reliability diagnostics, Python/shell execution policy, skill permissions, memory safety, secret masking, audit records, context/event traces, local packaging, and frontend/backend regression coverage.

## Why This Stage

The first eight stages make Kira useful and extensible. Stage 09 makes it explainable and safer to use on real projects with local files, project indexes, Python scripts, workflow skills, graph resumes, transcript history, and memory.

## Scope

- Permission policy for file reads, Python execution, controlled shell execution, skill invocation, skill tools/actions, memory writes, and workflow external actions.
- Permission and diagnostics policy for provider config, provider selection, request overrides, and real smoke tests.
- Audit log for provider selection, tools, interrupts, resumes, Python runs, skill activation, workflow execution, and memory operations.
- Audit and diagnostics for transcript writes, summary regeneration, explicit compaction, tool-output replacement, fork/rollback, conversation archive/delete, and history context injection.
- Secret masking in config, events, audit, memory, and exported traces.
- Doctor/diagnostics endpoint.
- Context/event/retrieval/memory trace export.
- Transcript/context trace export.
- Replacement-output inspection policy for retained local blobs, with redaction and user-visible reason metadata.
- Reliability diagnostics for run locks, event sequence gaps, side-effect ledger status, retry attempts, stale checkpoints, and cancelled runs.
- Retrieval diagnostics for index health, stale files, ignored files, no-`rg` fallback, citation quality, and prompt-injection fixtures.
- Frontend and backend smoke tests.
- Functional frontend polish for diagnostics, empty/error/loading states, and keyboard-accessible controls needed to validate safety/observability flows.
- Local packaging instructions.

Excluded:

- Full OS sandbox.
- Cloud deployment.
- Team-level approvals.
- Unbounded or interactive shell.

## Inputs And Dependencies

- Stage 02 tool boundaries.
- Stage 04 storage.
- Stage 05 HITL.
- Stage 06 skill package contract and project knowledge retrieval.
- Stage 07 memory system.
- Stage 08 transcript and conversation context.
- Real LLM provider layer with config path, Minimax/custom presets, timeout/retry, fixture fallback, and stream mapping.

## Design

Permission decisions use a small action model:

| Action | Default |
| --- | --- |
| read provider readiness | allow with redacted status only |
| override provider/model per request | allow only configured profiles; ask or reject for unknown profiles |
| read project file | allow inside root unless ignored/sensitive |
| search project files | allow inside root with caps |
| run workspace Python script | ask when script or args are risky, otherwise allow with caps |
| run temp Python script | ask |
| run controlled shell command | allow for project-bound local runs with cwd, env, timeout, output, redaction, and audit caps |
| invoke local skill | allow if source is trusted and policy permits |
| invoke imported/remote skill | ask |
| skill workflow external action | ask unless skill policy marks it safe and project policy permits |
| write memory to session/projectLocal | allow for manual user action, ask for extracted candidates when risky |
| write memory to project/user | ask unless explicitly configured |
| archive/delete conversation transcript | allow for explicit user action, audit tombstone/summary invalidation |
| inspect retained replaced tool output | ask unless debug policy explicitly allows; always redact before display/export |
| fork conversation | allow explicit user action and record provenance |
| rollback conversation | allow explicit user action; never delete abandoned branch by default |

Audit records should include action, provider profile ID, model name, fixture fallback status, tool, skill, workflow, conversation ID, turn ID, thread ID, active head ID, event sequence, cwd/root, memory ID, project citation ID, compaction ID, replacement ID, or fork/rollback source when applicable, result status, timestamps, redacted args, and output summary. Secrets are redacted before persistence or export.

## Implementation Tasks

1. Implement permission action model.
2. Add audit tables and export.
3. Add secret masking utilities.
4. Apply redaction to provider config display, provider errors, events, audit, memory, and traces.
5. Add doctor endpoint for Python, `rg`, SQLite, provider config/key presence, optional provider smoke connectivity, graph reliability tables, skill manifests, project index, memory DB, and frontend/backend versions.
6. Add trace export for provider selection, provider attempts, transcript context, active parent chain, compaction, replacement stubs, context packing, events, retries, side-effect ledger, project retrieval citations, skill activation, memory citations, and replay.
7. Polish frontend safety/observability surfaces: empty states, retry/reused-side-effect events, stop/resume controls, project knowledge panel, skill panel, memory inspector, diagnostics, and responsive behavior.
8. Add frontend smoke tests for welcome, run, event stream, tool schemas, skills, memory, and HITL.
9. Document local packaging and startup commands.

## Validation

- Sensitive values are redacted in all exports.
- Provider selection, Python/shell execution, file access, skill activation, and memory writes are audited with redacted metadata.
- Transcript writes, summary regeneration, compaction, replacement inspection, fork/rollback, conversation archive/delete, and transcript context injection are audited with redacted metadata.
- Doctor identifies missing provider keys, invalid provider profiles, upstream smoke-test failures, missing `rg`, Python runtime issues, invalid skill manifests, project index problems, run lock anomalies, side-effect ledger anomalies, and memory DB problems.
- Trace export can reproduce key provider selection, context, event, retrieval, skill, graph reliability, and memory facts without secrets.
- Safety/observability frontend surfaces pass desktop and narrow viewport smoke tests.
- Frontend and backend smoke tests pass.

## Exit Criteria

- Kira can be used locally on real projects with understandable boundaries.
- Failures are inspectable through state, audit, memory citations, and trace output.
- The roadmap is ready to drive implementation specs or OpenSpec changes.

## Deferred Work

- Product-grade Web visual refinement lands in Stage 10.
- OS sandboxing, vector retrieval, cloud sync, sub-agents, remote skills, signed packages, and team workflows require separate roadmap decisions.
