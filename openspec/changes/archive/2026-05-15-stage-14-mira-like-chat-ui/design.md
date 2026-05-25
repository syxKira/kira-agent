## Visual Direction

Stage 14 uses the Stage 12 study in `docs/mira-frontend-study/` and the Stage 13
turn model to build a light, conversation-first UI:

- off-white canvas;
- user bubble on the right;
- assistant identity row on the left;
- continuous answer body rather than repeated assistant cards;
- subtle action bar after answers;
- collapsed `思考过程` and inline tool activity;
- bottom sticky composer.

## Debug Boundary

The default chat surface must not expose operator/debug UI by default. Skills,
project knowledge, memory, trace, audit, and diagnostic surfaces can remain
available through explicit debug routes, drawers, environment-gated toggles, or
future refined inspector design.

## Dependency Boundary

Stage 14 may introduce small stable dependencies for markdown, collapsibles,
tooltips, icons, or visual interaction when they improve user experience and are
isolated behind Kira components. It must not import cis-mira's full design
system, state model, service hooks, tracking, or rich editor stack without a
separate explicit proposal.

## Interface Impact

- Backend: none required.
- Frontend: replaces the default shell and message components.
- Shared schemas: none.
- Persistence: none.
- Safety: hidden thinking, tool output, secrets, replacement stubs, and audit
  boundaries remain separate from visible answer text.

## Testing Impact

Component tests should assert structure: right user bubble, assistant identity,
one assistant answer region, collapsed thinking, no default inspector, and empty
composer after submit. Stage 15 adds browser screenshots.
