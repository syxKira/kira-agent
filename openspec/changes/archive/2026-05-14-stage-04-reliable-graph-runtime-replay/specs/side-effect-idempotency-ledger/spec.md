## ADDED Requirements

### Requirement: Stable idempotency keys

The system SHALL generate stable idempotency keys for side-effect-capable graph tool calls and external actions using thread ID, checkpoint ID, node name, call index, tool/action name, and arguments hash.

#### Scenario: Same call gets same key
- **WHEN** the same checkpointed tool call is evaluated during resume
- **THEN** the generated idempotency key matches the original key

#### Scenario: Different arguments get different key
- **WHEN** a tool call changes arguments
- **THEN** the generated idempotency key changes

### Requirement: Side-effect ledger lifecycle

The system SHALL record side-effect ledger entries with idempotency key, thread ID, checkpoint ID, node, tool/action, redacted args hash, status, result hash, summary, external reference when present, and audit reference when present.

#### Scenario: Ledger records planned and completed
- **WHEN** a side-effect-capable tool call starts and completes
- **THEN** the ledger records status transitions and a bounded result summary

#### Scenario: Ledger stores redacted args
- **WHEN** a ledger entry is persisted
- **THEN** raw secrets and raw provider config are not stored in args or result summaries

### Requirement: Completed side effects are reused

The system SHALL reuse completed ledger results on resume or replay rather than re-running side-effect-capable actions.

#### Scenario: Resume reuses completed result
- **WHEN** a resume reaches a side-effect call with a completed ledger entry
- **THEN** the runtime reuses the stored result and emits a side-effect reuse event

#### Scenario: Replay does not execute side effect
- **WHEN** debug replay includes side-effect history
- **THEN** replay reads the ledger and does not execute the tool/action again

### Requirement: Unknown side-effect status requires repair

The system SHALL stop automatic resume when a side-effect ledger entry has unknown status and SHALL require repair or reconciliation metadata before continuation.

#### Scenario: Unknown status blocks resume
- **WHEN** resume reaches a side-effect entry marked `unknown`
- **THEN** the run is marked repair-required and does not re-run the action automatically

#### Scenario: Repair records decision
- **WHEN** a developer resolves an unknown side-effect status
- **THEN** the ledger stores the repair decision and replay includes it

### Requirement: Non-idempotent side effects are not retried automatically

The system SHALL NOT automatically retry non-idempotent side-effect actions unless a stable dedupe key and safe retry policy are available.

#### Scenario: Non-idempotent failure stops
- **WHEN** a non-idempotent side-effect action fails
- **THEN** the runtime records the failure and stops for repair instead of retrying automatically
