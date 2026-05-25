## ADDED Requirements

### Requirement: Workbench renders doctor diagnostics
The frontend SHALL render doctor diagnostics for provider readiness, fixture fallback, runtime storage, Python, `rg`, skills, project index, memory, run locks, side-effect ledger, and version metadata with accessible empty/loading/error states.

#### Scenario: Missing real provider key
- **WHEN** doctor reports no valid real provider key and fixture fallback is available
- **THEN** the workbench SHALL show a warning and fixture fallback status without exposing raw config values

### Requirement: Workbench renders audit and trace surfaces
The frontend SHALL provide functional controls to fetch and inspect bounded redacted audit records and trace exports for the active run, conversation, memory, or project context.

#### Scenario: Inspect run trace
- **WHEN** a run completes and trace export is requested
- **THEN** the workbench SHALL show provider/context/event/retrieval/memory/transcript facts and truncation metadata without hidden thinking as assistant answer text

### Requirement: Workbench renders permission and safety states
The frontend SHALL display structured permission decisions, approval-required states, denied actions, inactive branch resume conflicts, replacement inspection denials, retry states, reused side effects, and diagnostics errors in the existing workbench layout.

#### Scenario: Denied replacement inspection
- **WHEN** replacement inspection is denied by policy
- **THEN** the workbench SHALL show the denial reason, replacement metadata, and audit reference without raw replaced output

### Requirement: Workbench safety surfaces are keyboard-accessible
Safety and observability controls SHALL be reachable by keyboard and SHALL avoid overlapping text or controls at desktop and narrow widths.

#### Scenario: Narrow viewport diagnostics
- **WHEN** diagnostics, audit, and trace panels are rendered in a narrow viewport
- **THEN** text SHALL wrap within containers and controls SHALL remain reachable without visual overlap
