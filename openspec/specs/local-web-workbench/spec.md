# local-web-workbench Specification

## Purpose
TBD - created by archiving change stage-01-local-web-foundation. Update Purpose after archive.
## Requirements
### Requirement: Render welcome screen

The system SHALL render a Vite React welcome screen as the first viewport for the local Kira app.

#### Scenario: Welcome screen starts without run events

- **WHEN** the frontend loads before any run has started
- **THEN** it shows `Kira Agent`, local project/model or fixture readiness, and a primary Start action without requiring backend event data

#### Scenario: Start enters workbench

- **WHEN** the user clicks Start
- **THEN** the frontend transitions to the run workbench without requiring a model call

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

### Requirement: Support desktop and narrow layouts

The system SHALL render the welcome screen and workbench without overlapping text or controls on desktop and narrow viewport sizes.

#### Scenario: Responsive workbench remains readable

- **WHEN** the workbench is viewed on desktop and narrow viewport widths
- **THEN** timeline content wraps cleanly, controls remain usable, and the inspector collapses or reflows away from the primary timeline

### Requirement: Render HITL timeline states

The workbench SHALL render Stage 05 interrupt and resume events as first-class timeline states.

#### Scenario: Interrupt row appears in timeline

- **WHEN** the event stream emits an `interrupt` event
- **THEN** the timeline shows a waiting-for-user row with the interrupt title and kind

#### Scenario: Resume row appears in timeline

- **WHEN** the event stream emits a `resume` event
- **THEN** the timeline shows a user decision marker without exposing raw internal resume payloads

### Requirement: Render active HITL control panel

The workbench SHALL show an active HITL control panel when the latest unresolved event is an interrupt.

#### Scenario: Approval controls are usable

- **WHEN** an approval interrupt is active
- **THEN** the panel provides approve and reject controls that are reachable by keyboard and pointer

#### Scenario: Edit controls preserve suggested content

- **WHEN** an edit interrupt is active
- **THEN** the panel initializes editable text from the interrupt payload and allows the user to submit a bounded edited value

#### Scenario: Question controls submit answer

- **WHEN** a question interrupt is active
- **THEN** the panel allows the user to enter and submit an answer matching the declared response fields

### Requirement: Workbench remains compatible with previous events

The workbench SHALL continue to render Stage 01 fixture, Stage 03 graph tool, Stage 04 replay, and direct provider events while adding Stage 05 HITL rendering.

#### Scenario: Fixture run still renders

- **WHEN** a run emits only Stage 01 fixture-style events
- **THEN** the workbench renders the existing timeline without requiring HITL state

#### Scenario: Side-effect reuse remains a tool/status block

- **WHEN** a run emits `side_effect_reused`
- **THEN** the workbench renders it as a non-answer status/tool block

#### Scenario: Provider metadata remains redacted

- **WHEN** timeline or panel payloads include provider metadata
- **THEN** raw API keys do not appear in the DOM

### Requirement: Workbench keeps selected conversation
The workbench SHALL create or select a conversation and SHALL pass its `conversation_id` on follow-up runs.

#### Scenario: First prompt creates selected conversation
- **WHEN** the user submits a prompt with no selected conversation
- **THEN** the frontend uses the returned `conversation_id` as the selected conversation

#### Scenario: Follow-up reuses conversation
- **WHEN** the user submits a second prompt after a run completed
- **THEN** the frontend sends the selected `conversation_id` in the run creation request

### Requirement: Workbench renders prior transcript
The workbench SHALL load and render prior visible transcript messages for the selected conversation before and alongside the current stream.

#### Scenario: Transcript restores after refresh
- **WHEN** the frontend loads with a selected conversation or user selects one from the conversation list
- **THEN** it fetches the transcript and renders prior visible user and assistant messages without requiring SSE replay

#### Scenario: Hidden thinking is not transcript UI
- **WHEN** a previous run emitted `thinking_delta`
- **THEN** the transcript view does not render that thinking content as assistant answer text

### Requirement: Conversation list is available in the workbench
The workbench SHALL provide a functional conversation list/create/select surface without requiring Stage 10 visual redesign.

#### Scenario: User switches conversations
- **WHEN** the user selects a different active conversation
- **THEN** the workbench loads that conversation's transcript
- **THEN** the next run uses that conversation ID

### Requirement: Context inspector shows transcript context
The workbench context inspector SHALL show conversation history and tool summary ContextItems when they are included or omitted for a run.

#### Scenario: Inspector shows history inclusion
- **WHEN** a run includes conversation history ContextItems
- **THEN** the context inspector displays their kind, role, turn/message IDs, trust label, budget cost, and omission/truncation status when applicable

### Requirement: Workbench exposes basic compaction controls
The workbench SHALL provide a minimal conversation compaction action in the existing side surface without requiring Stage 10 visual redesign.

#### Scenario: User triggers compaction
- **WHEN** the user selects a conversation and activates the compact action
- **THEN** the frontend calls the conversation compact API
- **THEN** the workbench refreshes transcript and context metadata for that conversation

#### Scenario: Compaction error is visible
- **WHEN** compaction fails
- **THEN** the frontend shows a bounded error state without exposing raw provider errors or secrets

### Requirement: Workbench shows compaction summaries in context inspector
The context inspector SHALL display `conversation_summary` and `compaction_summary` ContextItems with source IDs, stale status, summarizer metadata, trust label, and budget decisions.

#### Scenario: Inspector shows included summary
- **WHEN** a run context trace includes a compaction summary
- **THEN** the inspector displays the summary kind, summary ID, covered turn/message range, stale status, budget cost, and inclusion status

#### Scenario: Inspector shows stale or omitted summary
- **WHEN** a summary is stale or omitted from provider context
- **THEN** the inspector displays the stale or omission reason without showing raw hidden thinking or secrets

### Requirement: Workbench shows replacement stubs safely
The workbench SHALL display replacement stub metadata for tool-output replacements without exposing raw replaced output.

#### Scenario: Inspector shows replacement metadata
- **WHEN** a run context trace or transcript contains replacement metadata
- **THEN** the workbench displays replacement ID, reason, omitted count, source part ID, retention policy, and bounded summary
- **THEN** raw replacement content is not rendered

### Requirement: Transcript rendering distinguishes summaries from answers
The workbench SHALL render compaction and replacement metadata as transcript/context metadata rather than normal visible assistant answer text.

#### Scenario: Restored transcript excludes summary as answer
- **WHEN** a conversation transcript is restored after compaction
- **THEN** prior assistant answer text remains visible as answer text
- **THEN** compaction summaries and replacement stubs are visually or structurally distinct metadata rows

### Requirement: Workbench exposes basic fork controls
The workbench SHALL provide a minimal control to fork a selected conversation from a visible transcript message or turn without requiring Stage 10 visual redesign.

#### Scenario: User forks from transcript message
- **WHEN** the user selects a valid transcript message and activates fork
- **THEN** the frontend calls the fork API
- **THEN** the new conversation becomes selectable and its transcript/context reflects the fork point

### Requirement: Workbench exposes basic rollback controls
The workbench SHALL provide a minimal control to roll back a conversation active head to a selected active-chain message or turn.

#### Scenario: User rolls back conversation
- **WHEN** the user selects a valid active-chain message and activates rollback
- **THEN** the frontend calls the rollback API
- **THEN** the conversation transcript and context metadata refresh to show the new active head and inactive branch metadata

### Requirement: Workbench shows branch and active-head metadata
The workbench SHALL display active head, fork source, rollback transition, and inactive branch omission metadata in existing conversation, transcript, or context inspector surfaces.

#### Scenario: Inspector shows inactive branch omission
- **WHEN** run context omits messages because they are outside the active branch
- **THEN** the context inspector displays the branch omission reason, message IDs, turn IDs, and active head metadata without raw secrets

### Requirement: Workbench shows resume conflicts
The workbench SHALL render structured resume conflict responses when a user attempts to resume an interrupted run outside the active branch.

#### Scenario: Resume conflict displayed
- **WHEN** resume returns an inactive-branch conflict
- **THEN** the frontend shows a bounded conflict state with thread ID, turn ID, active head ID, and suggested next action metadata
- **THEN** raw hidden thinking and provider secrets are not rendered

### Requirement: Workbench renders doctor diagnostics
The frontend SHALL render doctor diagnostics for provider readiness, fixture fallback, runtime storage, Python, `rg`, skills, project index, memory, run locks, side-effect ledger, and version metadata with accessible empty/loading/error states.

#### Scenario: Missing real provider key
- **WHEN** doctor reports no valid real provider key and fixture fallback is available
- **THEN** the workbench SHALL show a warning and fixture fallback status without exposing raw config values

### Requirement: Workbench renders audit and trace surfaces
The frontend SHALL provide functional controls to fetch and inspect bounded redacted audit records and trace exports for the active run, conversation, memory, or project context.

#### Scenario: Inspect run trace
- **WHEN** a run completes and trace export is requested
- **THEN** the workbench SHALL show provider/context/event/retrieval/memory/transcript facts and truncation metadata without hidden thinking as assistant answer text

### Requirement: Workbench renders permission and safety states
The frontend SHALL display structured permission decisions, approval-required states, denied actions, inactive branch resume conflicts, replacement inspection denials, retry states, reused side effects, and diagnostics errors in the existing workbench layout.

#### Scenario: Denied replacement inspection
- **WHEN** replacement inspection is denied by policy
- **THEN** the workbench SHALL show the denial reason, replacement metadata, and audit reference without raw replaced output

### Requirement: Workbench safety surfaces are keyboard-accessible
Safety and observability controls SHALL be reachable by keyboard and SHALL avoid overlapping text or controls at desktop and narrow widths.

#### Scenario: Narrow viewport diagnostics
- **WHEN** diagnostics, audit, and trace panels are rendered in a narrow viewport
- **THEN** text SHALL wrap within containers and controls SHALL remain reachable without visual overlap

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

