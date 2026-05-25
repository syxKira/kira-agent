## Reference Inputs

Primary reference project:

- `/Users/bytedance/Desktop/code-agent-set/cis-mira`

Important cis-mira areas:

- chat shell: `src/components/chat-layout/`
- message list: `src/routes/chat-page/components/messages/`
- reasoning: `message-item/deep-think-shell.tsx`,
  `message-item/thinking-line-clamp.tsx`
- assistant response: `message-item/agent-response-message.tsx`
- user prompt: `message-item/user-prompt/manus-user-prompt.tsx`
- composer: `src/components/prompt-input/prompt-input.tsx`
- stream handling: `src/features/stream/hooks/use-stream-base.ts`

## Design Choice

Kira uses cis-mira as a frontend experience reference, not as a direct
application dependency. The study must separate:

- Adopt: layout, message grouping, collapsed reasoning, tool process disclosure,
  composer clearing/focus, and answer action patterns.
- Adapt: markdown, collapsible, tooltip, icon, virtual-list, or visual-test
  dependencies when a clear user-experience need exists.
- Do not copy: cis-mira business adapters, tracking, sensitive-check services,
  internal design-system assumptions, multi-agent marketplace, and rich editor
  stack until Kira has matching requirements.

## Interface Impact

- Backend: none.
- Frontend: adds documentation that constrains later implementation.
- Shared schemas: none.
- Persistence: none.
- Safety: preserves hidden-thinking, no-secret, redaction, and bounded-output
  rules by documenting them as non-negotiable in the UI target.

## Testing Impact

This stage is documentation-focused. Verification is OpenSpec validation plus a
manual consistency pass that ensures every known frontend complaint maps to a
future stage.

