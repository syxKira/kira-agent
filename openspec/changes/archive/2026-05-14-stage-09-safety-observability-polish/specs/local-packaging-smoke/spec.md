## ADDED Requirements

### Requirement: Local packaging instructions are complete
The system SHALL document local startup, configuration, doctor checks, fixture fallback, real provider smoke prerequisites, backend tests, frontend tests, and common troubleshooting steps.

#### Scenario: New local install
- **WHEN** a user follows the documented local startup path
- **THEN** they SHALL be able to start FastAPI, start Vite, open the workbench, run fixture mode, run doctor, and identify whether real provider config is ready

### Requirement: Core smoke checks cover safety and observability
The repository SHALL include smoke checks for health, tools, provider readiness, doctor, run creation/events, skills, project retrieval, memory, transcript context, HITL, audit, and trace export.

#### Scenario: Smoke tests without real key
- **WHEN** smoke tests run in a clean local environment without real provider secrets
- **THEN** they SHALL pass using fixture fallback and SHALL NOT require network access by default
