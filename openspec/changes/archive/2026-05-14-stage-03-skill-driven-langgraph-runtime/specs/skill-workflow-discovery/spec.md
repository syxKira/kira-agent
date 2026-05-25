## ADDED Requirements

### Requirement: Workflow-capable skill discovery

The system SHALL discover workflow-capable skills using a minimal Stage 03 metadata convention that identifies a skill ID, display name, description, workflow declarations or factories, allowed tools, and workflow node metadata.

#### Scenario: Built-in test skill is discoverable

- **WHEN** the backend starts with the Stage 03 test skill available
- **THEN** the skill registry includes the test skill as workflow-capable with its workflow metadata

#### Scenario: Non-workflow skill is ignored by graph runtime

- **WHEN** a skill has no workflow declaration or workflow factory
- **THEN** the graph runtime does not expose it as workflow-capable

### Requirement: Safe skill metadata API

The system SHALL expose workflow-capable skill metadata through a backend API without exposing raw provider config, API keys, local file contents, or executable source code.

#### Scenario: Skill list returns public metadata only

- **WHEN** a client requests the skill metadata endpoint
- **THEN** the response includes skill IDs, names, descriptions, workflow names, allowed tools, and node metadata
- **THEN** the response does not include raw API keys, provider config objects, local file contents, or Python source code

#### Scenario: Empty skill registry is valid

- **WHEN** no workflow-capable skills are registered
- **THEN** the skill metadata endpoint returns an empty skills list rather than failing

### Requirement: Skill workflow selection

The system SHALL allow run creation to select a workflow-capable skill by `skill_id` while preserving existing runs that do not specify a skill.

#### Scenario: Run selects known skill

- **WHEN** a run creation request includes a known workflow-capable `skill_id`
- **THEN** the run record stores the selected skill and workflow metadata for graph execution

#### Scenario: Run omits skill

- **WHEN** a run creation request omits `skill_id`
- **THEN** the run uses the existing provider or fixture streaming path

#### Scenario: Run selects unknown skill

- **WHEN** a run creation request includes an unknown `skill_id`
- **THEN** the backend returns a structured validation error and does not create a graph run

### Requirement: Skill model hints are metadata, not secrets

The system SHALL treat skill model hints as provider selection inputs only after validation and SHALL NOT allow skill metadata to include raw API keys or raw provider configuration.

#### Scenario: Skill model hint is applied through provider selection

- **WHEN** a selected skill declares an allowed model hint and the request does not override the model
- **THEN** provider selection may use the skill model hint through the existing provider selection policy

#### Scenario: Skill metadata contains secret-like fields

- **WHEN** skill metadata attempts to declare an API key or raw provider config
- **THEN** the skill is rejected or the secret field is omitted from public metadata and graph state
