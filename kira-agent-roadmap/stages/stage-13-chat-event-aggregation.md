# Stage 13: Chat Event Aggregation

## Goal

Replace raw event-row rendering with a frontend chat view-model layer that turns
SSE events and transcript messages into coherent conversation turns.

## Why This Stage

The biggest visible Kira defect is not only CSS. It is the rendering model: one
run can emit many `text_delta`, `thinking_delta`, tool, checkpoint, retry, and
done events, and the UI can mistakenly show them as many independent assistant or
status cards. A Mira-like UI cannot be reliable until Kira renders turns instead
of raw events.

## Scope

- Add frontend-only view models for conversation turns, messages, reasoning
  groups, tool activities, and run display state.
- Merge all visible answer `text_delta` chunks for a run/turn into one assistant
  answer.
- Attach `thinking_delta`, `tool_start`, `tool_result`, `checkpoint`, `retry`,
  `interrupt`, `resume`, `done`, and `error` to the active turn.
- Render transcript history and live events through the same adapter.
- Treat `done` as state, not a prominent main card.

Excluded:

- No backend event contract change.
- No transcript persistence migration.
- No visual redesign beyond what is necessary to prove the aggregation model.

## Inputs And Dependencies

- Stage 12 study docs in `docs/mira-frontend-study/`, especially
  `message-streaming-model.md`, `reasoning-and-tools.md`, and
  `kira-target-ui-spec.md`.
- Existing `KiraEvent` schemas and transcript APIs.
- Stage 08 transcript/compaction/fork/rollback behavior.
- Stage 11 components for thinking and tool activity as provisional UI pieces.

## Design

The frontend should introduce a narrow adapter, for example:

```ts
type ChatTurnViewModel = {
  id: string;
  user?: ChatMessageViewModel;
  assistant?: ChatMessageViewModel;
  reasoning: ReasoningGroupViewModel[];
  tools: ToolActivityViewModel[];
  statuses: RunStatusViewModel[];
  runState: "idle" | "streaming" | "waiting" | "completed" | "error" | "cancelled";
};
```

The exact field names can evolve, but the invariant cannot: React components
render turn view models. They do not directly map every raw event to a visible
message card.

Mapping rules:

| Event or Source | Mapping |
| --- | --- |
| active prompt | current turn user message |
| transcript user/assistant | historical turn messages |
| `text_delta` | append to current assistant message |
| `thinking_delta` | append to current reasoning group |
| `tool_start` / `tool_result` | start or complete a tool activity |
| `checkpoint` / `retry` | compact process status |
| `interrupt` / `resume` | HITL turn state |
| `done` | terminal state only |
| `error` | error state with concise visible failure |

## Implementation Tasks

1. Add chat view-model types and a pure event aggregation module under `web/src/`.
2. Add fixtures for interleaved text/thinking/tool/checkpoint/done streams.
3. Update the workbench render path to consume aggregated turns.
4. Ensure existing transcript rows are normalized into the same turn model.
5. Remove or bypass direct per-event answer rendering for `text_delta`.
6. Move `done` rendering to subtle state/composer metadata.
7. Add unit tests for aggregation, event ordering, transcript/live merge, and
   hidden-thinking exclusion.

## Validation

- `pnpm test` from `kira-agent/web`.
- `pnpm typecheck` from `kira-agent/web`.
- `openspec validate stage-13-chat-event-aggregation --type change --strict`.
- Manual fixture check: one prompt with many `text_delta` chunks renders one
  assistant answer.

## Exit Criteria

- The UI cannot show one run's answer as multiple scattered `Assistant` cards.
- `Completed` is no longer a prominent timeline card.
- Tool and thinking content remain inspectable but separate from answer text.

## Deferred Work

- Full Mira-like visual layout lands in Stage 14.
- Browser screenshot regression lands in Stage 15.
