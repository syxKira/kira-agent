## MODIFIED Requirements

### Requirement: Expose redacted provider metadata

The system SHALL expose provider selection decisions and provider attempt outcomes in redacted run/provider metadata, state projection, persisted attempts, event payloads, and replay/debug export.

#### Scenario: Run response includes provider metadata

- **WHEN** a run is created
- **THEN** the response includes provider mode, source, model when applicable, preset or provider name when applicable, and fallback reason when applicable, with no raw API key

#### Scenario: Stream events include provider metadata safely

- **WHEN** remote, fixture, or graph stream events are emitted
- **THEN** event metadata may include redacted provider selection and attempt details but never raw API key

#### Scenario: State projection includes provider attempt

- **WHEN** a provider is attempted during a graph node
- **THEN** state projection and replay expose redacted provider profile, model, retry count, timeout, fallback flag, and final status

### Requirement: Preserve excluded stages

The system SHALL NOT implement Stage 05 HITL UI, Stage 06 project knowledge retrieval, Stage 07 memory, production remote deployment, or a general shell as part of provider selection or provider attempt persistence.

#### Scenario: Provider attempts do not add future-stage systems

- **WHEN** Stage 04 persists provider selection and attempt metadata
- **THEN** it does not create memory records, project retrieval indexes, or user-facing HITL approval UI

## ADDED Requirements

### Requirement: Coordinate provider retry exhaustion with graph retry

The system SHALL make provider retry exhaustion visible to the graph retry policy in structured, redacted metadata.

#### Scenario: Provider retry exhaustion is recorded

- **WHEN** the provider adapter exhausts its retry budget
- **THEN** graph runtime records the provider attempt failure class and retry count without leaking secrets

#### Scenario: Graph retry respects provider budget

- **WHEN** graph retry policy considers retrying a provider node after adapter exhaustion
- **THEN** it retries only if the node remains safe and graph retry attempts remain
