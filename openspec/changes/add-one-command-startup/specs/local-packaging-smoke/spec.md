## ADDED Requirements

### Requirement: Local packaging smoke covers one-command startup
The repository SHALL include local smoke coverage or documented manual smoke steps for both one-command development startup and one-command single-service startup.

#### Scenario: One-command development smoke
- **WHEN** the one-command development smoke path runs in a clean local fixture environment
- **THEN** it verifies that the managed backend and frontend become reachable
- **THEN** it verifies that the Vite frontend can reach `/api/health` through same-origin proxying
- **THEN** it verifies that the managed processes can be stopped cleanly

#### Scenario: One-command single-service smoke
- **WHEN** the one-command single-service smoke path runs after or during frontend build preparation
- **THEN** it verifies that one FastAPI origin serves `GET /`
- **THEN** it verifies that the same origin serves `GET /api/health`
- **THEN** it verifies that a fixture run can be created and streamed without a real provider key

### Requirement: Local packaging documentation includes one-command paths
The local packaging documentation SHALL describe the one-command development path, the one-command single-service path, required prerequisites, configuration flags, and troubleshooting behavior.

#### Scenario: New user follows one-command development docs
- **WHEN** a new local user follows the documented one-command development path
- **THEN** they can open the printed frontend URL
- **THEN** they can run a fixture-backed flow without manually starting a second terminal

#### Scenario: New user follows one-command serve docs
- **WHEN** a user follows the documented one-command serve path
- **THEN** they can open the printed FastAPI URL
- **THEN** the frontend and backend operate from the same origin
- **THEN** the docs explain that this mode does not add authentication, TLS, or public internet hardening

#### Scenario: Troubleshooting documents partial startup failures
- **WHEN** frontend build, backend startup, dependency installation, port binding, or provider configuration is not ready
- **THEN** the documentation identifies the likely cause and the command or configuration needed to proceed
