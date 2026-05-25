## MODIFIED Requirements

### Requirement: Timeline renders event-specific Stage 11 chat rows

The frontend SHALL map normalized Kira events to visually distinct Stage 11 timeline rows or cards without depending on raw provider or LangGraph payload shapes, SHALL render assistant answer rows as tight chat bubbles without an oversized vertical gap between the row label and the answer text, and SHALL render tool activity inline so the conversation itself shows what the agent did.

#### Scenario: Normalized events have distinct visual treatment

- **WHEN** the timeline receives `text_delta`, `thinking_delta`, `tool_start`, `tool_result`, `checkpoint`, `interrupt`, `resume`, `retry`, `side_effect_reused`, `error`, or `done` events
- **THEN** it SHALL render answer text in a tight chat bubble layout, subdued collapsible `思考过程` blocks, compact `调用工具` rows, expandable tool-result cards, debug checkpoint markers, HITL waiting rows, user decision markers, retry attempt rows, reuse markers, error blocks, and completion rows as separate visual treatments

#### Scenario: Assistant answer row has no oversized gap

- **WHEN** an assistant answer row is rendered for a `text_delta` event or transcript message
- **THEN** the row SHALL group the `Assistant` label, answer text, and timestamp inside one chat bubble container with controlled spacing
- **THEN** the rendered row SHALL NOT introduce an oversized vertical white-space gap between the `Assistant` label and the answer text at desktop or narrow widths

#### Scenario: Hidden thinking is not answer text

- **WHEN** `thinking_delta` and `text_delta` events are present in the same run
- **THEN** hidden thinking SHALL remain in subdued collapsible `思考过程` UI
- **THEN** hidden thinking SHALL NOT be merged into normal assistant answer text, persisted visible transcript rows, copyable answer content, or screenshot fixtures that represent final answers

#### Scenario: Tool activity is visible without the inspector

- **WHEN** the timeline receives `tool_start` and `tool_result` events
- **THEN** it SHALL render tool activity inline in the chat timeline with a `调用工具` header or equivalent localized label, tool name, status, timestamp, and bounded preview metadata
- **THEN** the user SHALL be able to understand which tool ran and inspect a bounded result preview without opening a right-side inspector

#### Scenario: Tool output stays separate from answers

- **WHEN** a tool result contains JSON, text, file-search output, or an error payload
- **THEN** the result SHALL render inside a tool activity card with wrapping, bounded height, and expand/collapse behavior for long content
- **THEN** the result SHALL NOT be concatenated into assistant answer text, hidden thinking text, or transcript answer rows

### Requirement: Hidden thinking renders as a collapsible block

The frontend SHALL group consecutive `thinking_delta` events into one collapsible `思考过程` block per run segment, render it closed by default, and expose a clear toggle so the user can read the hidden thinking on demand without exposing it as answer text.

#### Scenario: Thinking block defaults to collapsed

- **WHEN** the timeline first renders one or more `thinking_delta` events for a run segment
- **THEN** the thinking block SHALL be rendered closed by default with a `思考过程` label and a toggle affordance
- **THEN** the hidden thinking text SHALL NOT be visible until the user opens the block

#### Scenario: Thinking block opens and closes via toggle

- **WHEN** the user activates the thinking block toggle by pointer or keyboard
- **THEN** the block SHALL expand to show the joined hidden thinking text in a subdued style
- **THEN** activating the toggle again SHALL collapse the block back to its closed default

#### Scenario: New run resets the thinking block

- **WHEN** a new run or new turn begins after a previous run produced thinking
- **THEN** the previous run's thinking block SHALL remain collapsed in history without leaking into the new run's answer
- **THEN** the new run's thinking SHALL accumulate into a fresh collapsible block independent of prior runs
