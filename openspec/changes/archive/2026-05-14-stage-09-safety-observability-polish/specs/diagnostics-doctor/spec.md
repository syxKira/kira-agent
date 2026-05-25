## ADDED Requirements

### Requirement: Doctor reports local readiness
The system SHALL expose a read-only doctor diagnostic response for backend, frontend, provider config, SQLite runtime storage, Python runtime, `rg` availability/fallback, skill manifests, project index, memory DB, run locks, side-effect ledger, and version metadata.

#### Scenario: Default doctor check
- **WHEN** `GET /api/doctor` is called without deep-check flags
- **THEN** the response SHALL include component statuses, severity, redacted messages, and remediation hints without requiring a real API key or network call

### Requirement: Provider diagnostics never expose keys
The doctor SHALL report provider config path, loaded status, configured profiles, default provider, model, preset/base URL status, key presence, and fixture fallback readiness without exposing raw API keys.

#### Scenario: Missing provider key
- **WHEN** no valid API key exists for the configured default provider
- **THEN** doctor SHALL report fixture fallback readiness and a warning without failing the local web loop

### Requirement: Deep checks are explicit
The system SHALL run expensive or external diagnostics only when explicitly requested by query parameter or future UI action.

#### Scenario: Optional provider smoke test
- **WHEN** no deep provider smoke flag is supplied
- **THEN** doctor SHALL NOT call the upstream provider and SHALL mark real smoke as skipped when appropriate
