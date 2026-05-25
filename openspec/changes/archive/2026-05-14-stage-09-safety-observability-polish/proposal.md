## Why

Kira now has real provider access, tools, graph runs, HITL, project retrieval, memory, transcript continuity, compaction, and fork/rollback. Stage 09 hardens those capabilities for regular local use by making boundaries explicit, actions auditable, diagnostics inspectable, and local setup verifiable before Stage 10 visual refinement.

## What Changes

- Add a local permission action model for provider overrides, project file reads/search, controlled Python execution, skill invocation/tool actions, memory writes, transcript operations, replacement inspection, and workflow external actions.
- Add a redacted audit log for provider selection, run lifecycle, tool calls, Python runs, project retrieval, skill activation, HITL interrupts/resumes, memory operations, transcript writes/compaction/replacement/fork/rollback, and cancellation.
- Add a doctor/diagnostics API and CLI-friendly response that checks provider config/key presence, SQLite/runtime tables, Python availability, `rg` fallback, skill manifests, project index health, memory DB health, run locks, side-effect ledger anomalies, and frontend/backend version metadata.
- Add trace/export APIs for run context, provider attempts, events, retries, side-effect ledger, project retrieval citations, memory citations, transcript active-chain decisions, compaction/replacement metadata, and branch decisions, with secrets redacted before persistence/export.
- Add replacement-output inspection policy for retained local debug blobs, including explicit user-visible reason metadata and redaction before display or export.
- Add frontend safety/observability surfaces for diagnostics, audit/trace export, permission decisions, inactive/retry/error states, and no-secret/no-hidden-thinking display.
- Add local packaging and smoke-test documentation for starting the backend/frontend, verifying doctor output, and running core regression tests.

Non-goals:

- No OS sandbox, cloud deployment, team approvals, remote auth, remote skill signing, vector database, cloud memory sync, or general shell.
- No project file mutation tools, patch tools, git workflows, LSP diagnostics, or code-agent profile.
- No Stage 10 product-grade visual redesign, dark cockpit, task rail overhaul, or final interaction polish.
- No broad business workflow implementation in Kira core; workflows remain skill-defined.

## Capabilities

### New Capabilities

- `safety-permission-policy`: Local action model, default decisions, permission metadata, and enforcement boundaries for provider, tools, Python, skills, memory, transcript, replacement inspection, and workflow actions.
- `audit-log`: Redacted local audit records and export behavior for safety-relevant runtime actions.
- `diagnostics-doctor`: Doctor checks and readiness diagnostics for local install, provider config, runtime storage, tools, skills, retrieval, memory, graph reliability, and frontend/backend versions.
- `observability-trace-export`: Redacted trace/export contract for run, context, provider, tool, retrieval, memory, transcript, graph reliability, and replay facts.
- `local-packaging-smoke`: Local packaging docs and smoke-test acceptance checks for dependable local startup and regression coverage.

### Modified Capabilities

- `llm-provider-selection`: Provider selection decisions become permission-aware, auditable, doctor-checkable, and export-safe.
- `controlled-python-execution`: Python execution gains Stage 09 permission decisions, audit records, diagnostics, and trace export metadata while remaining non-shell execution.
- `project-knowledge-retrieval`: Retrieval/indexing gains permission/audit/diagnostic metadata for ignored/stale files, no-`rg` fallback, citation quality, and prompt-injection fixtures.
- `memory-lifecycle`: Memory writes, lifecycle actions, extraction decisions, and retrieval citations gain permission, audit, and redacted trace behavior.
- `conversation-transcript-core`: Transcript writes, archive/delete, compaction, replacement, fork/rollback, active-chain context injection, and hidden-thinking boundaries gain audit and export metadata.
- `local-run-api`: APIs expose doctor, audit, trace export, permission decisions, and structured safety errors without leaking secrets.
- `local-web-workbench`: The workbench renders diagnostics, audit/trace export, permission decisions, and safety states with accessible empty/loading/error handling.

## Impact

- Backend: FastAPI routes, runtime storage migrations, provider selection, tool execution, project knowledge, memory service, transcript service, graph runtime integration, and redaction utilities.
- Frontend: API client/types, workbench inspector panels, diagnostics/audit/trace views, permission decision UI, and smoke tests.
- Shared contracts: JSON schemas for permission decisions, audit records, doctor diagnostics, trace export, and local smoke fixtures.
- Docs: README, server/web/src docs, and local packaging/startup instructions.
- Tests: backend unit/integration tests for policy/audit/doctor/export/redaction and frontend tests for diagnostics, safety states, and no-secret/no-hidden-thinking rendering.
