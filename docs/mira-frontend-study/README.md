# Mira Frontend Study For Kira

This directory records the frontend lessons Kira should take from
`/Users/bytedance/Desktop/code-agent-set/cis-mira` before the Stage 13-15
chat rebuild. It is an implementation guide for future Kira frontend work, not
a request to clone cis-mira's whole application stack.

## Reference Surface

Primary cis-mira files to study:

- `src/components/chat-layout/chat-page-ui.tsx`
- `src/components/chat-layout/chat-page-ui.module.less`
- `src/components/chat-layout/chat-footer-ui.tsx`
- `src/routes/chat-page/mira-page.tsx`
- `src/routes/chat-page/components/messages/manus-message-list.tsx`
- `src/routes/chat-page/components/messages/message-list-native-scroller.tsx`
- `src/routes/chat-page/components/messages/message-item/agent-message.tsx`
- `src/routes/chat-page/components/messages/message-item/agent-response-message.tsx`
- `src/routes/chat-page/components/messages/message-item/agent-reasoning-message.tsx`
- `src/routes/chat-page/components/messages/message-item/deep-think-shell.tsx`
- `src/routes/chat-page/components/messages/message-item/thinking-line-clamp.tsx`
- `src/routes/chat-page/components/messages/message-item/cot-tool-aggregate.tsx`
- `src/routes/chat-page/components/messages/message-item/user-prompt/manus-user-prompt.tsx`
- `src/components/prompt-input/prompt-input.tsx`
- `src/hooks/use-chat-manager.ts`
- `src/features/stream/hooks/use-stream-base.ts`
- `src/features/stream/hooks/pre-created-answer-shell-controller.ts`

Topic-specific notes:

- layout and scroll ownership: [`layout-and-shell.md`](layout-and-shell.md)
- stream-to-turn aggregation: [`message-streaming-model.md`](message-streaming-model.md)
- thinking and tool disclosure: [`reasoning-and-tools.md`](reasoning-and-tools.md)
- composer and answer actions: [`composer-and-actions.md`](composer-and-actions.md)
- Kira acceptance target: [`kira-target-ui-spec.md`](kira-target-ui-spec.md)

## Adopt

- Three-part chat shell: header, scrollable message content, sticky composer.
- Message-first rendering: UI is organized by conversation turns, not by raw
  backend events.
- Assistant response shape: one assistant response per turn, with model identity,
  readable markdown/body content, and a subdued action bar.
- Reasoning shape: collapsed-by-default thinking shell that can be opened on
  demand and does not masquerade as the answer.
- Tool activity shape: tool calls and results belong to the answer process, not
  to a separate operator dashboard.
- Composer behavior: submit clears the input, keeps focus, and shows stop/running
  controls without burying the conversation.
- Visual priority: the default surface is the conversation; diagnostics and
  inspector panels are secondary.

## Adapt

Kira can reuse component ideas and small utility dependencies when they directly
improve user experience, are stable, and can be isolated behind Kira's own
interfaces. Good candidates include collapsible primitives, markdown rendering,
tooltips, copy helpers, lightweight icon packages, virtualized list helpers only
after measured need, and browser-level visual testing support.

Kira should not import cis-mira's business data model. The Kira frontend needs a
thin adapter that maps existing `KiraEvent` and transcript payloads into Kira's
own chat view models.

Any future dependency proposal must state the user-facing benefit, isolation
boundary, bundle and maintenance cost, and test coverage. A dependency is not
acceptable if it requires adopting cis-mira service hooks, tracking, session
state, marketplace concepts, or rich-editor assumptions.

## Do Not Copy Blindly

- Large business state layers such as cis-mira's session-specific atoms, query
  caches, or message adapters.
- Internal product services, tracking, sensitive-check service hooks, and
  multi-agent marketplace behavior.
- Rich input editor stacks such as Slate unless Kira later needs structured
  attachments, mentions, slash commands, or rich editing as product requirements.
- Full design-system packages unless Kira explicitly commits to that design
  system and can support its dependency and token model.

## Kira Direction

Stage 12 records this study. Stage 13 fixes the core event-to-turn model. Stage
14 rebuilds the default UI into a Mira-like light conversation product. Stage 15
locks the result with screenshot and regression checks.
