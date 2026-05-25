## MODIFIED Requirements

### Requirement: Welcome screen is a dark one-agent launch view

The frontend SHALL render the first viewport as a centered dark Kira launch screen with exactly one Kira agent card whose subtitle reads `一个专业的数据agent助手`, no `FastAPI local` / `Read-only context` / `Auto or fixture` readiness chips, and a primary `立刻开始` action.

#### Scenario: Welcome screen shows one Kira agent

- **WHEN** the frontend loads before a user starts the workbench
- **THEN** it SHALL show `Kira Agent`, a centered Kira agent card whose subtitle reads `一个专业的数据agent助手`, and a primary `立刻开始` control
- **THEN** it SHALL NOT show readiness chips for `FastAPI local` / `Read-only context` / `Auto or fixture`, `Local Web Agent`, `Local agent`, multi-agent selection, marketing sections, decorative hero art, or hidden thinking content

#### Scenario: Welcome content is centered

- **WHEN** the welcome screen is rendered at desktop and narrow viewport widths
- **THEN** the welcome content SHALL be vertically and horizontally centered within the viewport without left-justified flush alignment

#### Scenario: Primary action enters workbench

- **WHEN** the user activates `立刻开始`
- **THEN** the frontend SHALL enter the workbench without requiring a model call
- **THEN** the workbench SHALL be ready to submit a prompt or run the deterministic fixture path according to existing provider-selection behavior

### Requirement: Workbench uses a dark local-agent cockpit layout

The frontend SHALL render the workbench as a dark local-agent chat surface with a task/session rail, sticky agent header, scrollable centered timeline with bounded max width, sticky bottom composer, and no default operator inspector, prominent inspector entry point, or fixture run buttons in the chat surface.

#### Scenario: Desktop workbench layout is chat-first

- **WHEN** the workbench is viewed at a desktop width
- **THEN** it SHALL show a left task rail, sticky agent header, centered timeline with a bounded max width, and a sticky bottom composer or running controls without overlapping text or controls
- **THEN** it SHALL NOT render the `Conversations` / `Skills` / `Memory` / `Project` / `Context` / `Safety` operator panels, a prominent `Inspector` button, or the `Run fixture` / `Run error fixture` / `Run HITL fixture` buttons in the default chat surface

#### Scenario: Narrow workbench keeps timeline primary

- **WHEN** the workbench is viewed at a narrow width
- **THEN** the task rail SHALL collapse or move behind drawer or header controls
- **THEN** the timeline and composer SHALL remain reachable and readable without horizontal overflow

#### Scenario: Rail brand copy reflects Kira positioning

- **WHEN** the workbench rail is rendered
- **THEN** the rail brand copy SHALL read `一个专业的数据agent助手` instead of `Local agent`

### Requirement: Workbench composer supports polished local agent control

The frontend SHALL render a bottom composer with model/profile or fixture/auto indicators, keyboard submit behavior, disabled/running states, visible focus styling, and clear-on-submit behavior that empties the input value after a successful submit and keeps focus on the input.

#### Scenario: Composer starts empty

- **WHEN** the workbench first renders
- **THEN** the composer input value SHALL be an empty string
- **THEN** any guidance such as asking the configured model a question SHALL appear as placeholder text only, not as a submitted value

#### Scenario: Composer submits without changing provider semantics

- **WHEN** the user submits the primary composer in auto mode
- **THEN** the frontend SHALL continue to create a run with existing auto provider-selection behavior
- **THEN** the UI SHALL display the selected or pending provider/profile metadata only through existing redacted frontend-safe data

#### Scenario: Composer clears input after submit

- **WHEN** the user submits a prompt and the run is successfully created
- **THEN** the composer input value SHALL be cleared to an empty string
- **THEN** keyboard focus SHALL remain on the composer input so the user can immediately type the next prompt without manually clearing prior text

#### Scenario: Running state protects duplicate submits

- **WHEN** a run is active
- **THEN** the composer SHALL prevent duplicate prompt submission and SHALL show the existing stop or progress control state without hiding the active timeline
