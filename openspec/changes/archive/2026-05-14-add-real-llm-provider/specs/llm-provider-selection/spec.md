## ADDED Requirements

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

The system SHALL expose provider selection decisions in redacted run/provider metadata.

#### Scenario: Run response includes provider metadata

- **WHEN** a run is created
- **THEN** the response includes provider mode, source, model when applicable, preset or provider name when applicable, and fallback reason when applicable, with no raw API key

#### Scenario: Stream events include provider metadata safely

- **WHEN** remote or fixture stream events are emitted
- **THEN** event metadata may include redacted provider selection details but never raw API key

### Requirement: Preserve excluded stages

The system SHALL NOT implement Stage 02 tools, LangGraph runtime, checkpointing, memory, project knowledge retrieval, skill workflow runtime, or a general shell as part of provider selection.

#### Scenario: Provider selection does not add graph runtime

- **WHEN** the provider change is implemented
- **THEN** run execution remains provider streaming only and does not compile or dispatch LangGraph workflows
