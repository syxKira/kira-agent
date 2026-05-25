## ADDED Requirements

### Requirement: Frontend design contract defines Stage 10 UI
The frontend SHALL include `web/DESIGN.md` as the authoritative Stage 10 design contract for Kira web UI tokens, layout regions, component states, timeline mapping, responsive behavior, accessibility rules, and screenshot acceptance checks.

#### Scenario: Design contract guides frontend edits
- **WHEN** a developer or coding agent changes the Kira web UI after Stage 10
- **THEN** `web/DESIGN.md` SHALL provide the color tokens, typography, spacing, component rules, timeline event treatments, responsive rules, and do/don't guidance needed to keep the UI consistent

#### Scenario: Design contract preserves safety boundaries
- **WHEN** `web/DESIGN.md` describes assistant thinking, provider metadata, tool output, transcript summaries, replacement stubs, diagnostics, audit, or trace surfaces
- **THEN** it SHALL state that hidden thinking is not answer text and raw provider secrets or sensitive replacement content are not rendered in frontend-safe views

### Requirement: Welcome screen is a dark one-agent launch view
The frontend SHALL render the first viewport as a dark Kira launch screen with exactly one Kira agent card, readiness chips, and a primary `Start Now` action.

#### Scenario: Welcome screen shows one Kira agent
- **WHEN** the frontend loads before a user starts the workbench
- **THEN** it SHALL show `Kira Agent`, a concise local-workflow subtitle, exactly one Kira agent card, provider/project/fixture readiness chips, and a primary `Start Now` control
- **THEN** it SHALL NOT show multi-agent selection, marketing sections, decorative hero art, or hidden thinking content

#### Scenario: Start Now enters workbench
- **WHEN** the user activates `Start Now`
- **THEN** the frontend SHALL enter the workbench without requiring a model call
- **THEN** the workbench SHALL be ready to submit a prompt or run the deterministic fixture path according to existing provider-selection behavior

### Requirement: Workbench uses a dark local-agent cockpit layout
The frontend SHALL render the workbench as a dark local-agent cockpit with a task/session rail, main timeline, assistant identity/status row, bottom composer or running controls, and optional inspector or drawer.

#### Scenario: Desktop workbench layout is scannable
- **WHEN** the workbench is viewed at a desktop width
- **THEN** it SHALL show a left task rail, centered timeline, visible Kira assistant identity, event timeline, bottom composer or running controls, and an inspector or drawer affordance without overlapping text or controls

#### Scenario: Narrow workbench keeps timeline primary
- **WHEN** the workbench is viewed at a narrow width
- **THEN** the task rail and inspector SHALL collapse or move behind drawer controls
- **THEN** the timeline and composer SHALL remain reachable and readable without horizontal overflow

### Requirement: Workbench renders polished run and readiness states
The frontend SHALL provide visually distinct and accessible states for idle, loading, running, paused for HITL, reconnecting, no-provider-key fixture fallback, error, cancelled, and completed runs.

#### Scenario: No provider key fallback is visible
- **WHEN** doctor or provider readiness data indicates that no valid real provider key is available and fixture fallback is allowed
- **THEN** the workbench SHALL show a redacted no-key or fixture-fallback state without exposing raw config values

#### Scenario: Run lifecycle states remain actionable
- **WHEN** a run is idle, loading, running, paused for HITL, reconnecting, errored, cancelled, or completed
- **THEN** the composer, stop control, retry/resume affordances, and status rows SHALL reflect the current state with keyboard-reachable controls where an action already exists

### Requirement: Workbench composer supports polished local agent control
The frontend SHALL render a bottom composer with model/profile or fixture/auto indicators, context/action controls, keyboard submit behavior, disabled/running states, and visible focus styling.

#### Scenario: Composer submits without changing provider semantics
- **WHEN** the user submits the primary composer in auto mode
- **THEN** the frontend SHALL continue to create a run with existing auto provider-selection behavior
- **THEN** the UI SHALL display the selected or pending provider/profile metadata only through existing redacted frontend-safe data

#### Scenario: Running state protects duplicate submits
- **WHEN** a run is active
- **THEN** the composer SHALL prevent duplicate prompt submission and SHALL show the existing stop or progress control state without hiding the active timeline
