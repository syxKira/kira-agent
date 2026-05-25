## 1. Chat Shell

- [x] 1.1 Implement the light Mira-like chat shell around the Stage 13 turn model.
- [x] 1.2 Keep the welcome screen centered with one Kira agent and `立刻开始`.
- [x] 1.3 Move default dashboard/debug metadata out of the main chat surface.

## 2. Message Components

- [x] 2.1 Render user prompts as right-aligned bubbles.
- [x] 2.2 Render assistant turns with identity row, continuous answer body, subtle timestamp, and action bar.
- [x] 2.3 Attach collapsed `思考过程` and inline tool activity to the assistant turn.
- [x] 2.4 Ensure `done` and process statuses remain subtle and do not become primary cards.

## 3. Composer

- [x] 3.1 Style the bottom composer for the Mira-like surface.
- [x] 3.2 Preserve clear-on-submit, input focus, stop/running state, and HITL resume behavior.

## 4. Tests

- [x] 4.1 Add component tests for default chat structure and absence of inspector/debug panels.
- [x] 4.2 Add tests for assistant answer continuity, thinking collapse, and composer clear/focus.
- [x] 4.3 Run `pnpm typecheck`, `pnpm test`, `pnpm build`, and `openspec validate stage-14-mira-like-chat-ui --type change --strict`.
