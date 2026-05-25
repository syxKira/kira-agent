# llm-provider-config Specification

## Purpose
TBD - created by archiving change add-real-llm-provider. Update Purpose after archive.
## Requirements
### Requirement: Load provider config outside project root

The system SHALL load real LLM provider config from `~/.kira-agent/config.yaml` by default and SHALL use `KIRA_CONFIG_PATH` when that environment variable is set.

#### Scenario: Default config path is used

- **WHEN** `KIRA_CONFIG_PATH` is not set
- **THEN** the backend looks for provider config at `~/.kira-agent/config.yaml`

#### Scenario: Override config path is used

- **WHEN** `KIRA_CONFIG_PATH` points to a readable config file
- **THEN** the backend loads provider config from that path instead of the default path

### Requirement: Validate provider config fields

The system SHALL support provider config fields for `api_key`, `base_url` or `baseURL`, `model`, `timeout`, `retry`, `provider`, `preset`, and default provider selection.

#### Scenario: Valid OpenAI-compatible config loads

- **WHEN** config contains provider type `openai`, API key, base URL, model, timeout, and retry settings
- **THEN** the backend creates an internal provider config suitable for OpenAI-compatible streaming

#### Scenario: Invalid config reports redacted error

- **WHEN** config is malformed or missing required non-secret fields for a real provider
- **THEN** readiness metadata reports a structured redacted config error and no raw API key

### Requirement: Provide Minimax Global preset

The system SHALL include a `Minimax Global` preset with `provider: openai` and `baseURL: https://api.minimax.io/v1`.

#### Scenario: Minimax preset fills base URL

- **WHEN** config selects preset `Minimax Global`
- **THEN** the backend uses provider type `openai` and base URL `https://api.minimax.io/v1` unless explicitly overridden by supported config

### Requirement: Provide custom OpenAI-compatible provider

The system SHALL support a custom OpenAI-compatible provider where `provider` defaults to `openai` and `baseURL` or `base_url` is user-provided.

#### Scenario: Custom provider defaults to openai

- **WHEN** config provides a custom base URL and omits provider type
- **THEN** provider type defaults to `openai`

### Requirement: Redact secrets everywhere

The system SHALL redact API keys in logs, API responses, diagnostics, run/provider metadata, tests, and frontend readiness state.

#### Scenario: API key is redacted in public metadata

- **WHEN** provider readiness or run metadata is returned to a client
- **THEN** the response includes no raw API key and only a redacted key indicator when needed

#### Scenario: Error metadata is redacted

- **WHEN** config loading or provider selection fails
- **THEN** structured error metadata does not include raw API key content

### Requirement: Avoid committing API keys

The system SHALL document and enforce by default that API keys live outside the project root and are not committed to source control.

#### Scenario: Project local secret file is not required

- **WHEN** a developer runs backend tests or local fixture mode
- **THEN** no project-root API key file is required

