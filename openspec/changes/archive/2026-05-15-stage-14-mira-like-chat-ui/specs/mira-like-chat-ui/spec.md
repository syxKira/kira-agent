## ADDED Requirements

### Requirement: Default web UI is a Mira-like conversation surface

The frontend SHALL render the default Kira workbench as a light, conversation
first chat surface rather than an event dashboard.

#### Scenario: User and assistant messages follow chat layout

- **WHEN** a normal run is shown in the default workbench
- **THEN** the user prompt SHALL render as a right-aligned bubble
- **THEN** the assistant response SHALL render with a left-side identity row and one continuous answer body

#### Scenario: Dashboard elements are not default content

- **WHEN** the default chat surface loads
- **THEN** fixture controls, event counts, prominent completed cards, and operator inspector panels SHALL NOT be primary visible content
- **THEN** diagnostics SHALL be reachable only through explicit non-default debug affordances if retained

### Requirement: Assistant process is disclosed without overwhelming the answer

The frontend SHALL render reasoning and tool activity as part of the assistant
turn process while keeping the answer readable.

#### Scenario: Thinking is collapsed by default

- **WHEN** an assistant turn includes `thinking_delta` content
- **THEN** the UI SHALL show a collapsed `思考过程` disclosure by default
- **THEN** the thinking text SHALL remain separate from the assistant answer body

#### Scenario: Tool activity is inline process content

- **WHEN** an assistant turn includes tool calls or results
- **THEN** the UI SHALL show inline tool activity associated with that assistant turn
- **THEN** tool output SHALL NOT become answer body text

### Requirement: Composer remains a polished chat control

The frontend SHALL keep the bottom composer usable and quiet in the Mira-like
surface.

#### Scenario: Submit clears and refocuses

- **WHEN** the user submits a prompt successfully
- **THEN** the composer SHALL clear the submitted text
- **THEN** the input SHALL remain focused for the next prompt

#### Scenario: Running and HITL states stay reachable

- **WHEN** a run is streaming, stopped, interrupted, or waiting for resume input
- **THEN** the composer area SHALL expose the appropriate stop or HITL control without hiding the conversation timeline

