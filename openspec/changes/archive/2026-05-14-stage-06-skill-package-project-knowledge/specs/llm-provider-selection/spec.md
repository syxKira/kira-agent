## ADDED Requirements

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

