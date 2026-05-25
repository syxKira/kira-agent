# llm-provider-selection Specification

## Purpose
TBD - created by archiving change add-real-llm-provider. Update Purpose after archive.
## Requirements
### Requirement: Select default provider from config

The system SHALL select the default real provider and model from loaded provider config when valid credentials are available.

#### Scenario: Config default provider selected

- **WHEN** a run request does not force fixture and valid default provider config exists
- **THEN** the backend selects the configured provider and model for streaming

### Requirement: Support per-request provider and model override

The system SHALL allow run requests to override provider and model for that run without mutating saved config.

#### Scenario: Request model override selected

- **WHEN** a run request includes a model override
- **THEN** that run uses the requested model and exposes the selected model in redacted provider metadata

#### Scenario: Request provider override selected

- **WHEN** a run request includes a provider override matching a configured provider or preset
- **THEN** that run uses the requested provider for provider selection

### Requirement: Keep fixture provider available

The system SHALL keep fixture provider available for deterministic local runs and tests.

#### Scenario: Explicit fixture run remains deterministic

- **WHEN** a run request explicitly selects fixture mode or fixture script
- **THEN** the backend streams fixture events and does not call a remote LLM API

### Requirement: Fallback to fixture when API key is missing

The system SHALL degrade to fixture provider rather than failing the local web loop when no valid API key is available.

#### Scenario: Missing key falls back to fixture

- **WHEN** a real provider would otherwise be selected but no valid API key is available
- **THEN** run creation succeeds, provider selection uses fixture, and redacted metadata includes fallback reason `missing_api_key`

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

### Requirement: Coordinate provider retry exhaustion with graph retry

The system SHALL make provider retry exhaustion visible to the graph retry policy in structured, redacted metadata.

#### Scenario: Provider retry exhaustion is recorded

- **WHEN** the provider adapter exhausts its retry budget
- **THEN** graph runtime records the provider attempt failure class and retry count without leaking secrets

#### Scenario: Graph retry respects provider budget

- **WHEN** graph retry policy considers retrying a provider node after adapter exhaustion
- **THEN** it retries only if the node remains safe and graph retry attempts remain

### Requirement: Skill model hints participate in provider selection

The system SHALL allow validated skill model hints to participate in provider selection after explicit run request overrides and before configured defaults.

#### Scenario: Skill profile hint is selected
- **WHEN** a selected skill declares a configured provider profile hint and the run request does not override provider or model
- **THEN** provider selection may choose that configured profile and expose the decision in redacted metadata

#### Scenario: Request override wins over skill hint
- **WHEN** a run request supplies provider or model override and the selected skill also declares a model hint
- **THEN** the explicit request override takes precedence

### Requirement: Skill model hints cannot carry secrets

The system SHALL reject or omit skill model hints that include API keys, custom base URLs, authorization headers, or raw provider config objects.

#### Scenario: Secret-like model hint is rejected
- **WHEN** a skill manifest includes an API key or raw provider config in model metadata
- **THEN** validation rejects the hint and public skill metadata does not include the secret

### Requirement: Provider selection is permission-aware and audited
The system SHALL evaluate request provider/model overrides and skill provider hints through the permission policy before selecting a real provider, configured default, or fixture fallback.

#### Scenario: Unknown provider override
- **WHEN** a run requests an unknown provider profile
- **THEN** the system SHALL reject or ask according to policy, persist a redacted audit record, and avoid exposing raw config values

#### Scenario: Fixture fallback audit
- **WHEN** no valid API key is available and auto mode falls back to fixture
- **THEN** provider metadata, audit records, doctor output, and frontend readiness SHALL show redacted fallback reason metadata

### Requirement: Provider diagnostics are export-safe
Provider selection and attempt metadata SHALL be included in doctor and trace export responses only in redacted frontend-safe form.

#### Scenario: Provider failure includes secret text
- **WHEN** upstream provider errors include an API key-like token or configured secret value
- **THEN** state, replay, audit, doctor, trace export, and UI SHALL redact the secret

