## ADDED Requirements

### Requirement: Render welcome screen

The system SHALL render a Vite React welcome screen as the first viewport for the local Kira app.

#### Scenario: Welcome screen starts without run events

- **WHEN** the frontend loads before any run has started
- **THEN** it shows `Kira Agent`, local project/model or fixture readiness, and a primary Start action without requiring backend event data

#### Scenario: Start enters workbench

- **WHEN** the user clicks Start
- **THEN** the frontend transitions to the run workbench without requiring a model call

### Requirement: Render run workbench

The system SHALL render a timeline-style workbench with prompt composer, event timeline, running state, stop control state, and compact inspector placeholder.

#### Scenario: Idle workbench shows composer

- **WHEN** no run is active
- **THEN** the bottom bar shows a prompt composer ready to start a fixture-backed run

#### Scenario: Running workbench shows stop control

- **WHEN** a fixture-backed run is active
- **THEN** the bottom bar replaces or disables the composer with a Stop control state and running progress summary

### Requirement: Render Stage 01 timeline events

The system SHALL render fixture-backed events as timeline groups for user prompt, assistant status, fixture tool-card preview, visible assistant text, error, and done states.

#### Scenario: Fixture run renders timeline groups

- **WHEN** the user starts a fixture-backed run from the workbench
- **THEN** the timeline shows a right-aligned user message, left-aligned status row, structured fixture card when present, visible assistant text, timestamps, and a completed state

#### Scenario: Error event renders concise failure row

- **WHEN** the SSE stream emits an `error` event
- **THEN** the timeline renders a concise error row without crashing or treating the error as assistant text

### Requirement: Keep hidden thinking out of answer blocks

The system SHALL NOT render hidden thinking as normal assistant answer text in the workbench.

#### Scenario: Thinking event is filtered from answer text

- **WHEN** the SSE stream emits `thinking_delta` followed by `text_delta`
- **THEN** only the `text_delta` content appears in normal assistant answer blocks

### Requirement: Support desktop and narrow layouts

The system SHALL render the welcome screen and workbench without overlapping text or controls on desktop and narrow viewport sizes.

#### Scenario: Responsive workbench remains readable

- **WHEN** the workbench is viewed on desktop and narrow viewport widths
- **THEN** timeline content wraps cleanly, controls remain usable, and the inspector collapses or reflows away from the primary timeline
