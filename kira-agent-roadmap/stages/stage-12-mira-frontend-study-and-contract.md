# Stage 12: Mira Frontend Study And Contract

## Goal

Create a durable frontend study and design contract that captures what Kira
should learn from cis-mira's chat experience before any further UI rewrite.

## Why This Stage

Stage 11 fixed several visible defects, but the remaining problem is structural:
Kira still inherits too much of an event workbench mental model. This stage makes
the cis-mira reference explicit so implementation agents can rebuild Kira with a
shared target instead of repeatedly rediscovering layout, streaming, reasoning,
tool, and composer patterns.

## Scope

- Study cis-mira's chat layout, message list, reasoning UI, tool UI, composer,
  stream handling, and action patterns.
- Add `docs/mira-frontend-study/` with focused learning documents.
- Define dependency policy: do not import cis-mira's whole stack, but allow
  small stable dependencies when they directly improve user experience.
- Update Kira frontend design guidance to treat Stage 13-15 as the new main
  frontend rebuild sequence.

Excluded:

- No implementation of the new UI.
- No backend API changes.
- No adoption of cis-mira's product-specific services, state model, tracking, or
  multi-agent marketplace behavior.

## Inputs And Dependencies

- Stage 10 and Stage 11 frontend documents.
- `/Users/bytedance/Desktop/code-agent-set/cis-mira`.
- User feedback that the current Kira UI still scatters answer blocks, overstates
  completed state, and feels far from the desired Mira-like conversation.

## Design

The study should separate three categories:

| Category | Meaning |
| --- | --- |
| Adopt | Interaction and layout patterns Kira should reproduce |
| Adapt | Patterns that need a Kira-specific adapter or small dependency |
| Do not copy | cis-mira business architecture that would make Kira hard to maintain |

The core contract is: Kira owns its API and event model; cis-mira informs the
conversation experience.

## Implementation Tasks

1. Create `docs/mira-frontend-study/README.md`.
2. Add focused notes for layout/shell, message streaming model,
   reasoning/tools, composer/actions, and the target Kira UI spec.
3. Record the dependency rule in the study docs and the OpenSpec change.
4. Cross-link Stage 12-15 from the roadmap overview.
5. Confirm that future stages reference these docs rather than Stage 11 alone.

## Validation

- `openspec validate stage-12-mira-frontend-study-and-contract --type change --strict`.
- Manual consistency pass: every known user complaint maps to either Stage 13,
  Stage 14, or Stage 15.
- The docs mention exact cis-mira source files and avoid vague "make it better"
  language.

## Exit Criteria

- Future frontend agents can read the study docs and understand the target chat
  product direction before editing Kira.
- The dependency policy is explicit and permits useful UX dependencies without
  dragging in cis-mira's entire application stack.

## Deferred Work

- Actual event aggregation belongs to Stage 13.
- Actual Mira-like UI implementation belongs to Stage 14.
- Screenshot regression belongs to Stage 15.

