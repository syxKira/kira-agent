# Message Streaming Model Study

## cis-mira Pattern

cis-mira does not render every stream fragment as a standalone message. It builds
message objects and updates the relevant message content as streaming progresses.
Relevant reference files:

- `src/features/stream/hooks/use-stream-base.ts`
- `src/features/stream/hooks/pre-created-answer-shell-controller.ts`
- `src/routes/chat-page/components/messages/manus-message-list.tsx`
- `src/routes/chat-page/components/messages/message-list-native-scroller.tsx`
- `src/routes/chat-page/components/messages/message-item/agent-message.tsx`

Important patterns:

- user messages and agent messages are distinct first-class records;
- reasoning and final response can be adjacent but are not the same answer;
- a response shell may exist before final text is complete, but it is not shown
  as an independent empty answer card;
- updates are batched so the UI does not briefly show reasoning growth while the
  answer shell is missing;
- the latest streaming primary message is tracked so loading indicators appear
  on the right block at the right phase.

The transferable lesson is the invariant, not the implementation stack: Kira
should produce one turn view model per prompt/run and update that model as
events arrive. It should not import cis-mira stream hooks, session atoms,
tracking calls, or service adapters.

## Kira Problem To Fix

Kira currently receives normalized `KiraEvent` entries, but Stage 11 still maps
events too directly to timeline rows. This creates product bugs:

- a single assistant answer can be split into multiple `Assistant` blocks;
- `done` can become a visible `Completed` card that looks like answer content;
- tool and reasoning events appear beside the answer instead of being part of
  the same turn process;
- transcript history and live stream events can follow different rendering paths.

## Kira View Model

Stage 13 should introduce a frontend-only adapter:

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

The exact TypeScript shape can evolve, but the invariant is stable: components
render turns, not raw SSE events.

## Mapping Rules

| Input | Kira Mapping |
| --- | --- |
| active prompt | current turn user message |
| transcript user message | historical turn user message |
| transcript assistant message | historical turn assistant answer |
| `text_delta` | append to one assistant answer for the current turn |
| `thinking_delta` | append to current turn reasoning group |
| `tool_start` / `tool_result` | append or complete a current turn tool activity |
| `checkpoint` / `retry` | status metadata on current turn |
| `interrupt` / `resume` | HITL state on current turn |
| `done` | mark current turn complete; do not render a primary completed card |
| `error` | mark current turn error and render a concise failure state |

## Acceptance Invariant

For one user prompt, the visible answer should be one assistant response block
even when the stream contains many deltas, tool events, checkpoints, retries, or
done events.
