## 1. Shared Contracts

- [x] 1.1 Add JSON schemas for permission decisions, permission errors, audit records, doctor diagnostics, trace export, replacement inspection, and Stage 09 smoke fixtures.
- [x] 1.2 Extend provider, run-state, run-replay, run-context-trace, memory, project-knowledge, and conversation transcript schemas with audit IDs, permission metadata, doctor status, and trace/export references.
- [x] 1.3 Export frontend TypeScript types for permission decisions, audit records, doctor diagnostics, trace export responses, replacement inspection responses, and structured safety errors.
- [x] 1.4 Add shared examples proving secrets, hidden thinking, raw provider config, and raw replacement blobs are redacted.
- [x] 1.5 Validate all shared schema JSON files and example fixtures.

## 2. Storage And Redaction

- [x] 2.1 Add idempotent SQLite migrations for audit records and any persisted permission/diagnostic/export metadata.
- [x] 2.2 Add storage repository methods to create, list, filter, and export audit records by thread, conversation, project root, memory ID, action, status, and time range.
- [x] 2.3 Add central redaction helpers for API keys, bearer tokens, cookies, private keys, `.env` secrets, provider config, hidden thinking, and high-risk personal/customer fields.
- [x] 2.4 Apply redaction before audit insert, trace export serialization, doctor responses, permission responses, and replacement inspection responses.
- [x] 2.5 Add storage tests for audit migration idempotency, audit filters, redaction before persistence, bounded export limits, and existing Stage 04-08 data readability.

## 3. Permission Policy

- [x] 3.1 Implement a backend permission service with action IDs, subject metadata, decisions `allow`/`ask`/`deny`, redacted reasons, and audit correlation metadata.
- [x] 3.2 Define default decisions for provider readiness, provider/model override, project file read/search, controlled Python execution, skill invocation/action, memory write/lifecycle, transcript archive/delete/compact/fork/rollback, workflow external action, and replacement inspection.
- [x] 3.3 Add structured permission errors and approval-required responses for API routes.
- [x] 3.4 Add unit tests for deterministic default policy decisions without real provider keys or network access.
- [x] 3.5 Add no-secret tests for permission decisions and permission error responses.

## 4. Audit Integration

- [x] 4.1 Audit provider selection, provider attempts, fixture fallback, provider errors, and request overrides with redacted provider/model metadata.
- [x] 4.2 Audit tool dispatch, controlled Python execution, project file tools, project retrieval/index refresh/search, and replacement creation/inspection.
- [x] 4.3 Audit skill catalog activation, workflow selection, tool allowlist use, workflow execution start/end, retry, cancellation, side-effect reuse, and HITL interrupt/resume.
- [x] 4.4 Audit memory create/update/delete/lifecycle/extraction/retrieval/citation operations with guard decisions and redacted candidate metadata.
- [x] 4.5 Audit transcript writes, context injection, compaction, summary refresh, replacement stubs, fork, rollback, archive, delete/tombstone, and branch omissions.
- [x] 4.6 Ensure non-critical audit write failure records a diagnostic without breaking the local web loop.
- [x] 4.7 Add backend integration tests covering audit records for provider, Python, project retrieval, skill/HITL, memory, transcript, compaction, replacement, fork/rollback, and cancellation paths.

## 5. Doctor Diagnostics

- [x] 5.1 Add `GET /api/doctor` with default read-only checks for backend version, frontend version metadata, provider config loaded/key presence, fixture fallback, SQLite runtime DB, migrations, Python, `rg`, skills, project index, memory DB, run locks, side-effect ledger, and audit storage.
- [x] 5.2 Add optional deep-check flags for provider smoke connectivity and heavier storage/index checks, skipped by default.
- [x] 5.3 Report severity, status, component, redacted message, remediation hint, and evidence references for each doctor check.
- [x] 5.4 Add tests for healthy local fixture setup, missing provider key, invalid provider profile, missing `rg` fallback, Python runtime failure, invalid skill manifest, stale project index, memory DB issue, run lock anomaly, and side-effect ledger anomaly.
- [x] 5.5 Ensure doctor responses never include raw API keys, hidden thinking, raw memory secret candidates, or raw replacement blobs.

## 6. Trace And Export APIs

- [x] 6.1 Add read-only trace export endpoint(s) for a run/thread with provider selection, provider attempts, context inclusion/omission, event sequence, retries, checkpoint summaries, side-effect ledger, audit IDs, and terminal status.
- [x] 6.2 Add conversation trace export with active parent chain, branch metadata, inactive omissions, compaction summaries, replacement stubs, and transcript context decisions.
- [x] 6.3 Add project retrieval trace export with root, index health, skipped/omitted files, stale markers, citation IDs, ranking metadata, no-`rg` fallback, and prompt-injection fixture diagnostics.
- [x] 6.4 Add memory trace export with retrieval query, selected/omitted memory IDs, score reasons, citations, guard decisions, lifecycle events, and audit IDs.
- [x] 6.5 Add bounded export limits, cursors/time filters, summary-only defaults for large payloads, and truncation metadata.
- [x] 6.6 Add tests proving trace/export calls are read-only and do not run providers, execute tools, refresh indexes, mutate memory, mutate transcripts, acquire run locks, or append events.

## 7. Replacement Inspection

- [x] 7.1 Add replacement inspection API gated by replacement retention policy and permission decision.
- [x] 7.2 Return redacted inspected content or structured policy denial with replacement ID, hash prefix, reason, omitted count, retention policy, and audit record ID.
- [x] 7.3 Ensure raw sensitive replacement output is never returned in frontend-safe traces, audit export, doctor output, or default transcript responses.
- [x] 7.4 Add tests for allowed inspection, denied inspection, redacted secret output, missing replacement, invalid retention policy, and audit creation.

## 8. Subsystem Policy Integration

- [x] 8.1 Wire permission/audit into provider selection and provider readiness without changing fixture fallback behavior.
- [x] 8.2 Wire permission/audit into controlled Python execution while preserving cwd/env/timeout/output caps and no-shell behavior.
- [x] 8.3 Wire permission/audit into project file tools and project knowledge retrieval without adding mutation tools.
- [x] 8.4 Wire permission/audit into skill invocation, workflow selection, workflow external action metadata, and ToolNode allowlist behavior.
- [x] 8.5 Wire permission/audit into memory writes, extraction candidate decisions, lifecycle actions, retrieval citations, and guard failures.
- [x] 8.6 Wire permission/audit into transcript context injection, compaction, replacement stubs, fork/rollback, archive, and explicit delete/tombstone behavior.
- [x] 8.7 Add regression tests proving Stage 01-08 core flows still work with fixture fallback and no real API key.

## 9. Frontend Workbench

- [x] 9.1 Add API client functions for doctor diagnostics, audit list/export, trace export, permission decision preview or safety errors, and replacement inspection.
- [x] 9.2 Add workbench diagnostics surface with component statuses, severity, remediation hints, provider readiness, fixture fallback, Python, `rg`, storage, skills, project index, memory, run lock, side-effect ledger, and version metadata.
- [x] 9.3 Add audit/trace inspector surface for active run, selected conversation, project context, and memory context with bounded result display and truncation metadata.
- [x] 9.4 Render structured permission denied/approval-required states, unsafe provider override, unsafe Python execution, unsafe memory write, unsafe transcript delete, inactive branch resume conflict, and replacement inspection denial.
- [x] 9.5 Improve empty/loading/error states and keyboard reachability for diagnostics, audit, trace, and replacement inspection controls in the existing layout.
- [x] 9.6 Add frontend tests for doctor rendering, audit rendering, trace export rendering, permission denial display, replacement inspection denial, inactive branch resume conflict, no-secret rendering, hidden-thinking exclusion, and narrow-layout DOM checks.

## 10. Docs, Packaging, And Smoke Tests

- [x] 10.1 Document local startup, provider config, fixture fallback, doctor checks, audit/trace export, replacement inspection policy, and common troubleshooting in README/server/web/src docs.
- [x] 10.2 Document local packaging/start commands and smoke-test commands for backend, frontend, and shared contracts.
- [x] 10.3 Add backend smoke tests for health, provider status, doctor, tools, skills, run events, project retrieval, memory, transcript context, HITL, audit, and trace export.
- [x] 10.4 Add frontend smoke tests for welcome/workbench run, diagnostics, audit/trace panels, memory/project/skill panels, HITL, errors, and no-secret display.
- [x] 10.5 Run backend tests with `uv run --extra dev pytest`.
- [x] 10.6 Run frontend tests and typecheck/build with `pnpm test` and `pnpm build`.
- [x] 10.7 Run shared schema validation for `src/schemas`.
- [x] 10.8 Run `openspec validate "stage-09-safety-observability-polish" --strict`.
- [x] 10.9 Run `openspec status --change "stage-09-safety-observability-polish"` and confirm the change is ready for implementation.
