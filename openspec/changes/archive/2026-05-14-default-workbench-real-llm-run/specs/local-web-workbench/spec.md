## MODIFIED Requirements

### Requirement: Render run workbench

The system SHALL render a timeline-style workbench with prompt composer, event timeline, running state, stop control state, compact inspector placeholder, and explicit fixture/demo controls.

#### Scenario: Idle workbench shows composer

- **WHEN** no run is active
- **THEN** the bottom bar shows a prompt composer ready to start an auto provider-selected LLM run

#### Scenario: Default Run uses auto provider selection

- **WHEN** the user submits the main prompt composer with the Run action
- **THEN** the frontend creates a run with `provider_mode: "auto"`
- **THEN** the frontend does not pass `fixture` for that run

#### Scenario: Explicit fixture run remains available

- **WHEN** the user clicks the explicit `Run fixture` control
- **THEN** the frontend creates a run with fixture mode and the deterministic welcome fixture

#### Scenario: Running workbench shows stop control

- **WHEN** a run is active
- **THEN** the bottom bar replaces or disables the composer with a Stop control state and running progress summary

### Requirement: Render Stage 01 timeline events

The system SHALL render fixture-backed events as timeline groups for user prompt, assistant status, fixture tool-card preview, visible assistant text, error, and done states, while keeping the primary composer path independent of fixtures.

#### Scenario: Fixture run renders timeline groups

- **WHEN** the user starts a fixture-backed run from an explicit fixture control
- **THEN** the timeline shows a right-aligned user message, left-aligned status row, structured fixture card when present, visible assistant text, timestamps, and a completed state

#### Scenario: Error event renders concise failure row

- **WHEN** the SSE stream emits an `error` event
- **THEN** the timeline renders a concise error row without crashing or treating the error as assistant text

### Requirement: Keep hidden thinking out of answer blocks

The system SHALL NOT render hidden thinking as normal assistant answer text in the workbench.

#### Scenario: Thinking event is filtered from answer text

- **WHEN** the SSE stream emits `thinking_delta` followed by `text_delta`
- **THEN** only the `text_delta` content appears in normal assistant answer blocks
