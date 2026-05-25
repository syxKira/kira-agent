## Why

Kira's current frontend can still render raw run events too directly. That makes
one answer appear across multiple assistant blocks and lets terminal events such
as `done` become visually louder than the actual answer. A Mira-like chat UI
requires a frontend view-model layer that renders conversation turns, not raw SSE
events.

## Scope

- Add a frontend-only chat turn aggregation layer.
- Merge multiple answer `text_delta` chunks into one assistant response per run
  or turn.
- Attach thinking, tool, checkpoint, retry, HITL, done, and error events to the
  current turn as process state.
- Render transcript history and live events through the same turn model.
- Treat `done` as terminal state, not as a prominent main card.

## Non-Goals

- No backend event contract changes.
- No transcript persistence migration.
- No full visual redesign beyond what is necessary to prove aggregation.
- No new provider, skill, graph, memory, or safety semantics.

## Acceptance Criteria

- One prompt with many `text_delta` events renders one assistant answer.
- Interleaved thinking/tool/checkpoint/retry/done events do not split the
  assistant answer.
- `done` no longer renders as a prominent `Completed` primary card.
- Hidden thinking and tool output remain separate from answer text and transcript
  assistant answers.
- Existing HITL, transcript, provider, and safety tests still pass.

## Risks

- Transcript history and live events may diverge if they use different render
  paths. Mitigation: normalize both through the same turn adapter.
- Tool event correlation can be incomplete. Mitigation: preserve order and render
  unmatched tool results as process items without merging them into answers.

