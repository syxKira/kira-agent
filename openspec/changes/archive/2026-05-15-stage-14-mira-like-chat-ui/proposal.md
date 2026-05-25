## Why

The user-facing goal is not a darker or cleaner event log. Kira needs a default
conversation product experience close to the Mira reference: right-aligned user
bubbles, assistant identity, continuous answer content, subtle reasoning/tool
disclosure, and a quiet bottom composer.

## Scope

- Switch the default chat surface to a light Mira-like conversation layout.
- Render user prompts as right-aligned bubbles.
- Render assistant turns with model identity, continuous answer body, subdued
  action bar, collapsed `思考过程`, and inline tool activity.
- Remove default dashboard/debug elements from the primary chat surface.
- Keep diagnostics reachable only through explicit non-default affordances.
- Preserve composer clear-on-submit, stop/running state, HITL, transcript, and
  safety behavior.

## Non-Goals

- No backend API changes.
- No multi-agent marketplace or agent selector.
- No full cis-mira dependency stack.
- No rich editor unless a separate requirement establishes attachments, mentions,
  slash commands, or structured editing.

## Acceptance Criteria

- The default UI looks like a conversation assistant, not an event dashboard.
- One prompt produces one coherent assistant answer region.
- `思考过程` is collapsed by default and tool activity is part of the turn process.
- `Completed`, event counts, fixture controls, and inspector panels are not
  prominent in the default chat.
- The input clears and remains focused after successful submit.

## Risks

- Moving debug surfaces out of the default UI can reduce discoverability for
  developers. Mitigation: keep explicit debug routes/drawers documented.
- A light Mira-like shell can conflict with older dark Stage 10 guidance.
  Mitigation: Stage 14 supersedes Stage 10/11 as the default chat product
  surface while old debug surfaces may keep dark styling.

