## ADDED Requirements

### Requirement: Replay includes memory usage summaries
The run state and replay/debug export APIs SHALL include frontend-safe summaries of memory retrieval, injected memory citations, and extraction candidates associated with a run.

#### Scenario: Replay shows injected memory
- **WHEN** replay/debug export is requested for a run with injected memory
- **THEN** the export includes memory IDs, citation IDs, scopes, types, score reasons, and redacted source summaries

#### Scenario: Replay omits raw memory secrets
- **WHEN** replay/debug export includes memory summaries
- **THEN** raw memory secrets, raw provider secrets, and unbounded candidate text are absent

### Requirement: Replay does not rerun memory extraction
The replay/debug export SHALL read persisted memory summaries and SHALL NOT rerun memory retrieval, extraction, providers, tools, or lifecycle actions.

#### Scenario: Replay is read-only for memory
- **WHEN** a completed run's replay is requested
- **THEN** no new memory record, candidate, citation, event, or retrieval trace is created
