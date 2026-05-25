## Event-To-Turn Adapter

Stage 13 follows `docs/mira-frontend-study/message-streaming-model.md` and adds
a frontend adapter that consumes:

- visible transcript messages;
- current active prompt;
- live `KiraEvent` stream entries.

The adapter outputs turn view models. Components render those view models instead
of rendering each raw event as a primary timeline row.

Representative shape:

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

The exact names are not API contracts; the turn invariant is the contract.

## Mapping

| Source | Mapping |
| --- | --- |
| transcript user message | historical turn user |
| transcript assistant message | historical turn assistant |
| active prompt | current turn user |
| `text_delta` | append to current turn assistant text |
| `thinking_delta` | append to current turn reasoning |
| `tool_start` / `tool_result` | add or complete current turn tool activity |
| `checkpoint` / `retry` | compact process status |
| `interrupt` / `resume` | HITL state |
| `done` | terminal state only |
| `error` | error state |

## Interface Impact

- Backend: none.
- Frontend: new pure aggregation module and components consuming turn models.
- Shared schemas: none.
- Persistence: none.
- Safety: strengthens hidden-thinking and tool-output separation by moving those
  into dedicated turn fields.

## Testing Impact

Unit tests should focus on pure aggregation. Component tests should verify the
workbench uses the adapter and no longer renders raw `text_delta` and `done`
events as independent primary cards.
