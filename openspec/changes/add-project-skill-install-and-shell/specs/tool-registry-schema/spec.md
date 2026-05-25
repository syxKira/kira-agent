## ADDED Requirements

### Requirement: Tool registry exposes shell metadata

The tool metadata API SHALL include the controlled shell tool schema when the server registers it.

#### Scenario: Shell tool metadata is listed

- **WHEN** a client requests `GET /api/tools`
- **THEN** the response SHALL include `run_shell_command` with JSON Schema arguments, standard result schema, and `controlled_shell_execution` risk metadata
