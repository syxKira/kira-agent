# Stage 14: Mira-like Chat UI

## Goal

Rebuild Kira's default web experience into a Mira-like light conversation UI that
prioritizes the user/assistant dialogue over runtime diagnostics.

## Why This Stage

Stage 13 makes the data model safe to render. Stage 14 uses that model to replace
the current workbench feel with the requested product experience: right-aligned
user bubbles, assistant identity and continuous answer content, subtle process
disclosure, and a quiet bottom composer.

## Scope

- Switch the default chat surface to a light/off-white Mira-like visual language.
- Keep a centered welcome screen with one Kira agent and `立刻开始`.
- Render user messages as right-aligned soft bubbles.
- Render assistant turns with a model/agent identity row, continuous answer body,
  and subdued action bar.
- Render `思考过程` collapsed by default and tool activity as part of the answer
  process.
- Remove default inspector, fixture buttons, event count, and dashboard metadata
  from the main user surface.
- Keep debug/trace/diagnostic capabilities behind explicit non-default routes,
  drawers, or developer affordances.
- Preserve composer clear-on-submit and focus behavior.

Excluded:

- No new backend API requirement.
- No multi-agent selection.
- No full cis-mira dependency stack.
- No rich editor unless a specific Kira input requirement is added.

## Inputs And Dependencies

- Stage 12 study docs in `docs/mira-frontend-study/`, especially
  `layout-and-shell.md`, `composer-and-actions.md`, and
  `kira-target-ui-spec.md`.
- Stage 13 chat turn view models.
- Existing provider, transcript, HITL, memory, skill, project retrieval, and
  safety semantics.

## Design

Default visual behavior:

| Element | Treatment |
| --- | --- |
| Canvas | light/off-white, calm, low contrast |
| User prompt | right-aligned rounded neutral bubble |
| Assistant identity | left-side model/agent row, readable name |
| Assistant answer | continuous content block, not repeated cards |
| Actions | subtle copy/feedback/more icons below the answer |
| Thinking | collapsed `思考过程` disclosure |
| Tools | inline process rows/cards under the turn |
| Done | hidden/subtle state, never a loud card |
| Composer | bottom sticky input, clear primary action, stop while running |

The UI can introduce small stable dependencies for markdown, collapsible
behavior, tooltips, icons, or visual tests when those dependencies directly
improve user experience and stay isolated behind Kira components.

## Implementation Tasks

1. Create or refactor chat shell components around the Stage 13 turn model.
2. Replace event-card answer rendering with assistant turn rendering.
3. Implement the light Mira-like theme and responsive layout.
4. Add assistant identity, answer body, action bar, and subtle timestamp.
5. Keep thinking/tool process disclosure attached to the turn.
6. Move diagnostics and fixture controls out of the default chat surface.
7. Update welcome and composer styling to match the new surface.
8. Update tests for default visual structure and removed dashboard elements.

## Validation

- `pnpm typecheck` from `kira-agent/web`.
- `pnpm test` from `kira-agent/web`.
- `pnpm build` from `kira-agent/web`.
- `openspec validate stage-14-mira-like-chat-ui --type change --strict`.
- Manual browser review at desktop and narrow widths.

## Exit Criteria

- The default UI looks like a conversation product close to the Mira reference,
  not an event log or admin dashboard.
- A normal run shows one user bubble and one coherent assistant answer.
- Thinking, tools, HITL, and errors are understandable without overwhelming the
  answer.

## Deferred Work

- Rich text input, attachments, slash commands, and advanced message editing.
- Fully polished diagnostics UI.
- Theme switching.
