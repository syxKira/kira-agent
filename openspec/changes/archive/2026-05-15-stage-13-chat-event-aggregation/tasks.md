## 1. View Model Adapter

- [x] 1.1 Add chat turn, message, reasoning, tool activity, and status view-model types.
- [x] 1.2 Add a pure function that aggregates transcript messages, active prompt, and live events into ordered turns.
- [x] 1.3 Add fixtures for chunked text, interleaved thinking, tool calls, checkpoint/retry, HITL, done, and error events.

## 2. Workbench Integration

- [x] 2.1 Update the workbench timeline to render turn view models.
- [x] 2.2 Remove direct per-event `text_delta` assistant-card rendering from the default path.
- [x] 2.3 Render `done` as terminal state rather than a prominent card.
- [x] 2.4 Keep unmatched process events visible as subdued process/status content.

## 3. Tests

- [x] 3.1 Add unit tests proving many `text_delta` chunks render as one assistant answer.
- [x] 3.2 Add tests proving thinking and tool output do not merge into answer text.
- [x] 3.3 Add tests proving transcript and live events share the same rendering model.
- [x] 3.4 Run `pnpm test`, `pnpm typecheck`, and `openspec validate stage-13-chat-event-aggregation --type change --strict`.
