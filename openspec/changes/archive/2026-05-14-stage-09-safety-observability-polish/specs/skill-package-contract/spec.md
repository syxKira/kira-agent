## ADDED Requirements

### Requirement: Skill activation is permission-aware and audited
Skill catalog activation, workflow selection, tool allowlist use, and skill-declared external actions SHALL be evaluated through the permission policy and persisted to redacted audit records.

#### Scenario: Imported skill invocation
- **WHEN** an imported or untrusted skill is selected for a run
- **THEN** the system SHALL ask or deny according to policy and SHALL expose frontend-safe reasons without loading raw provider secrets

### Requirement: Skill diagnostics appear in doctor and trace export
Doctor and trace export SHALL include skill manifest validity, source priority, shadowing, model hints, permission metadata, workflow validation status, and diagnostics without exposing skill-provided secrets.

#### Scenario: Invalid skill manifest
- **WHEN** a skill manifest is invalid
- **THEN** doctor SHALL report the invalid skill, severity, path/source metadata, and remediation hint while keeping the local web loop available
