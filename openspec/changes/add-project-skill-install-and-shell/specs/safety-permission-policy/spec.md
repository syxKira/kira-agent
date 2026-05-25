## ADDED Requirements

### Requirement: Shell execution is permission-aware and audited

Kira SHALL treat shell execution as a permissioned local action with redacted audit-compatible metadata.

#### Scenario: Shell permission preview exists

- **WHEN** a caller previews action `shell.run`
- **THEN** Kira SHALL return a structured permission decision with redacted command subject metadata

#### Scenario: Shell execution events avoid secrets

- **WHEN** shell output or metadata is returned through tool events, audit, trace, or replay
- **THEN** Kira SHALL redact recognized secret values before returning frontend-safe data

#### Scenario: Secret inspection commands are rejected

- **WHEN** the agent attempts to print `.env` files or secret environment variables through shell
- **THEN** Kira SHALL reject the command before execution with a structured secret-inspection error

#### Scenario: Missing credentials stop further tool use

- **WHEN** a shell command fails because a local credential or token is missing
- **THEN** the default agent loop SHALL remove tools from the follow-up provider turn
- **THEN** the assistant SHALL report the missing local credential without probing files or environment variables for secret values
