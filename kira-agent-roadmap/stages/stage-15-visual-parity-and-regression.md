# Stage 15: Visual Parity And Regression

## Goal

Lock the Stage 14 Mira-like chat experience with browser-level screenshot smoke
tests and regression checks for the highest-risk conversation states.

## Why This Stage

Kira's frontend issues are visual and interaction-heavy. Unit tests can prove
aggregation and state rules, but they cannot reliably catch scattered answer
cards, loud completed blocks, input residue, sticky composer overlap, or a UI
that drifts back into a dashboard. Stage 15 gives the frontend a durable visual
quality gate.

## Scope

- Add browser-level smoke coverage for welcome and chat states.
- Add deterministic fixtures for normal answer, streaming/status phase,
  reasoning, tool call, HITL, error, and long transcript.
- Define explicit screenshot failure conditions.
- Make visual checks runnable locally without a real provider key.
- Document how to update expected screenshots intentionally.

Excluded:

- No production visual-diff service requirement.
- No remote browser grid.
- No backend runtime changes beyond fixture support if already available.

## Inputs And Dependencies

- Stage 12 study docs in `docs/mira-frontend-study/`, especially
  `kira-target-ui-spec.md`.
- Stage 13 turn aggregation.
- Stage 14 Mira-like UI.
- Existing fixture provider and web dev server.

## Design

Visual checks should prefer deterministic local paths:

- fixture data instead of real provider responses;
- stable viewport sizes;
- stable timestamps or masked timestamp zones where practical;
- screenshots for desktop and narrow widths.

Failure conditions:

- one answer scattered across multiple assistant blocks;
- `Completed` shown as a prominent card;
- default inspector/debug panels visible;
- thinking expanded by default;
- composer still contains submitted prompt;
- text overlaps or horizontal scrolling appears in normal/narrow screenshots.

## Implementation Tasks

1. Add screenshot smoke runner or extend the existing frontend smoke script.
2. Add deterministic fixture states for the required conversation scenarios.
3. Add DOM assertions for failure conditions that screenshots alone may miss.
4. Add desktop and narrow viewport captures.
5. Document local commands and screenshot update policy.
6. Keep smoke checks independent from real LLM credentials.

## Validation

- `pnpm test` from `kira-agent/web`.
- `pnpm build` from `kira-agent/web`.
- Browser smoke command for desktop and narrow screenshots.
- `openspec validate stage-15-visual-parity-and-regression --type change --strict`.

## Exit Criteria

- The Mira-like UI has repeatable local visual evidence.
- Regressions back to event-log UI or dashboard-first UI fail tests before merge.
- Future frontend changes have a clear acceptance baseline.

## Deferred Work

- Pixel-perfect screenshot approval service.
- Per-browser matrix beyond the local development browser.
- Accessibility audit automation beyond the first smoke layer.
