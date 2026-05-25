## ADDED Requirements

### Requirement: Runs accept bounded skill and project context controls

The run creation API SHALL accept frontend-safe controls for explicit skill activation and optional project context retrieval without exposing provider secrets or mutating project files.

#### Scenario: Run opts into project context
- **WHEN** a run request includes a project root and project context query or scope
- **THEN** the backend may retrieve cited project ContextItems within budget before provider input assembly

#### Scenario: Run context controls are redacted
- **WHEN** run creation returns metadata for skill and project context
- **THEN** the response omits raw provider secrets, raw manifest secrets, and unbounded local file contents

### Requirement: Run context trace API is available

The system SHALL expose a frontend-safe run context trace endpoint that shows included, truncated, and omitted ContextItems.

#### Scenario: Context trace returns included and omitted items
- **WHEN** a client requests context trace for a known run
- **THEN** the response includes ContextItem summaries, citations, trust labels, budget costs, truncation status, and omission reasons

#### Scenario: Unknown run context returns not found
- **WHEN** a client requests context trace for an unknown run
- **THEN** the backend returns a structured not-found error

