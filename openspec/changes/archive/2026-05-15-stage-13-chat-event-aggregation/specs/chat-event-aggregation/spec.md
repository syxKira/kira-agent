## ADDED Requirements

### Requirement: Frontend renders conversation turns instead of raw events

The frontend SHALL aggregate transcript messages, the active prompt, and live
Kira events into conversation turn view models before rendering the default chat
timeline.

#### Scenario: Multiple text deltas become one answer

- **WHEN** one run emits multiple visible `text_delta` events
- **THEN** the frontend SHALL render them as one assistant answer for the current turn
- **THEN** the frontend SHALL NOT render each chunk as a separate `Assistant` card

#### Scenario: Process events do not split the answer

- **WHEN** `thinking_delta`, `tool_start`, `tool_result`, `checkpoint`, `retry`, or `done` events appear between answer text chunks
- **THEN** the frontend SHALL keep the visible answer as one assistant response
- **THEN** the process events SHALL render as reasoning, tool, status, or terminal state for the same turn

### Requirement: Done is terminal state, not primary content

The frontend SHALL treat `done` as a terminal run or turn state and SHALL NOT show
it as a prominent primary message card in the default chat.

#### Scenario: Done does not create loud Completed card

- **WHEN** a run completes normally and emits `done`
- **THEN** the frontend SHALL update the turn/composer state to completed or idle
- **THEN** the frontend SHALL NOT render a large `Completed` card as part of the main answer flow

### Requirement: Transcript and live events share one render model

The frontend SHALL normalize restored transcript history and active live events
through compatible turn view models.

#### Scenario: Restored transcript matches live conversation shape

- **WHEN** a conversation is restored from transcript and a follow-up run is started
- **THEN** prior visible messages and the live run SHALL appear in one ordered conversation timeline
- **THEN** hidden thinking, tool output, compaction summaries, and replacement stubs SHALL remain separate from visible assistant answer text

