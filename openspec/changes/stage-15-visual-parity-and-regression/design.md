## Visual Smoke Strategy

Stage 15 should use `docs/mira-frontend-study/kira-target-ui-spec.md` as the
failure-condition contract and deterministic local fixtures:

- no real provider key required;
- stable run transcripts and events;
- fixed desktop and narrow viewport sizes;
- dynamic fields masked or controlled where possible.

The smoke layer can be a Playwright-style browser test, an existing browser smoke
script extension, or another local browser runner already accepted by Kira's web
toolchain.

## Required States

- welcome screen;
- normal user prompt plus assistant answer;
- streaming/status phase;
- collapsed and expanded `思考过程`;
- tool activity with long JSON/text;
- HITL interrupt and resume;
- error state;
- long transcript.

## Failure Conditions

Visual or DOM checks should fail if:

- one answer appears as multiple assistant cards;
- `Completed` appears as a prominent primary card;
- default inspector/debug panels are visible;
- thinking is expanded by default;
- submitted prompt text remains in the composer after submit;
- message content overlaps controls or causes horizontal overflow.

## Interface Impact

- Backend: none required.
- Frontend: test fixtures and smoke runner only.
- Shared schemas: none.
- Persistence: none.

## Testing Impact

Stage 15 becomes the frontend visual gate after `pnpm test`, `pnpm typecheck`,
and `pnpm build`.
