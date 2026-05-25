## ADDED Requirements

### Requirement: Web chat binds to the current project root

The web workbench SHALL pass the configured current project root to skill catalog requests and run creation by default.

#### Scenario: Project skills appear in slash menu

- **WHEN** the current project root contains valid `.kira/skills` packages
- **THEN** the workbench SHALL request skills with that project root
- **THEN** valid user-invocable project skills SHALL appear in the slash skill menu

#### Scenario: Run payload includes project root

- **WHEN** a user submits a normal prompt from the workbench
- **THEN** the run creation payload SHALL include the current project root unless the user clears or overrides it
