## ADDED Requirements

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
