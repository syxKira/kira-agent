# local-packaging-smoke Specification

## Purpose
TBD - created by archiving change stage-09-safety-observability-polish. Update Purpose after archive.
## Requirements
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

### Requirement: Visual smoke checks cover Stage 10 web states
The repository SHALL include deterministic Stage 10 visual or screenshot smoke checks for the local web welcome screen, workbench shell, timeline cards, HITL states, errors, long content, and narrow viewport behavior.

#### Scenario: Desktop visual smoke covers welcome and workbench
- **WHEN** Stage 10 frontend smoke checks run in a local fixture environment without real provider secrets
- **THEN** they SHALL cover the dark one-agent welcome screen, desktop workbench shell, task rail, assistant identity, timeline, composer, inspector or drawer affordance, running timeline, tool card, HITL state, error state, and completed state

#### Scenario: Narrow visual smoke covers responsive layout
- **WHEN** Stage 10 frontend smoke checks run at a narrow viewport
- **THEN** they SHALL verify that the task rail and inspector collapse or move behind controls, the timeline remains readable, the composer remains reachable, and long text or JSON does not overlap adjacent controls

### Requirement: Accessibility smoke checks cover Stage 10 controls
The repository SHALL include Stage 10 smoke or test coverage for keyboard reachability, accessible names, focus styling, contrast-sensitive states, and hidden-thinking separation.

#### Scenario: Keyboard path covers core workflow
- **WHEN** accessibility smoke checks exercise the Stage 10 web UI
- **THEN** a keyboard-only path SHALL be able to start the workbench, submit a prompt or fixture run, stop a running run when available, expand a tool card, navigate inspector or drawer controls, and answer a HITL panel

#### Scenario: Safety boundaries are checked visually
- **WHEN** Stage 10 smoke fixtures include thinking content, provider metadata, replacement metadata, audit data, trace data, and secret-like strings
- **THEN** the visual or DOM checks SHALL confirm hidden thinking is not answer text and raw provider secrets or raw replacement content are not displayed in frontend-safe surfaces

### Requirement: Local smoke documentation includes Stage 10 visual checks
The local web documentation SHALL list the Stage 10 visual or screenshot smoke commands, fixture prerequisites, viewport coverage, and expected behavior when no real provider key is configured.

#### Scenario: New local developer can run visual smoke
- **WHEN** a developer follows the local web smoke documentation
- **THEN** they SHALL be able to run the Stage 10 visual checks against deterministic fixture data without network access or real provider keys by default

