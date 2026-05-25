# Reasoning And Tools Study

## cis-mira Pattern

cis-mira's reasoning UI is intentionally subordinate to the answer:

Relevant reference files:

- `src/routes/chat-page/components/messages/message-item/deep-think-shell.tsx`
- `src/routes/chat-page/components/messages/message-item/thinking-line-clamp.tsx`
- `src/routes/chat-page/components/messages/message-item/agent-reasoning-message.tsx`
- `src/routes/chat-page/components/messages/message-item/cot-tool-aggregate.tsx`
- `src/routes/chat-page/components/messages/message-item/agent-response-message.tsx`

- `DeepThinkShell` is collapsed by default.
- The header communicates a phase such as planning, working, or completed.
- Content is available on demand but does not create the visual weight of an
  answer card.
- Tool calls are part of the reasoning/content block structure and are rendered
  as process artifacts, not as separate assistant answers.

## Kira Target

Kira should keep hidden thinking, tool output, and answer text separate while
still making the process inspectable.

### Thinking

- Label: `思考过程`.
- Default state: collapsed.
- Open state: shows joined thinking text with subdued styling.
- Copy behavior: thinking is not included in answer copy.
- Transcript behavior: thinking is not restored as visible assistant answer text.

### Tools

- Label: `调用工具`.
- A `tool_start` starts a compact activity row.
- A matching `tool_result` completes the same activity when correlation metadata
  exists.
- Long results use bounded preview plus expand/collapse.
- Tool output never concatenates into answer text.
- Copy controls must respect existing redaction and bounded-output safeguards.

### Done And Reliability Events

- `done` should update the turn state and composer state.
- `retry`, `checkpoint`, and `side_effect_reused` are process/status metadata.
- None of these should appear as large primary answer cards in the default chat.

## Dependency Guidance

Kira may introduce a small collapsible primitive, tooltip library, icon package,
or copy helper if it improves accessibility and reduces custom UI risk. The
dependency must be isolated to Kira components and must not force adoption of
cis-mira's state, service, or product architecture.

Rejected imports include cis-mira sensitive-check service hooks, task/session
tracking, business message adapters, and any tool marketplace behavior. Kira
already has its own redaction, bounded output, hidden-thinking, transcript, and
audit boundaries; the UI must preserve those contracts.
