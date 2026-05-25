## Why

The most important remaining Kira frontend quality risks are visual: scattered
assistant answers, loud completed cards, default debug panels, input residue,
thinking expanded by default, and layout overlap. Unit tests are necessary but
not sufficient. The rebuilt UI needs browser-level visual smoke checks.

## Scope

- Add deterministic browser smoke coverage for welcome, normal chat, streaming,
  reasoning, tool activity, HITL, error, and long transcript states.
- Add desktop and narrow viewport checks.
- Add explicit failure conditions for the previous bad UI patterns.
- Keep smoke tests independent of real LLM credentials.
- Document how to run and intentionally update visual baselines.

## Non-Goals

- No production visual-diff service.
- No remote browser grid.
- No real provider smoke requirement for visual tests.
- No backend behavior change except using existing deterministic fixtures.

## Acceptance Criteria

- Local visual smoke can run without an API key.
- Screenshots cover the major conversation states.
- DOM or screenshot assertions fail when `Completed` is prominent, answers are
  scattered, default inspector panels appear, thinking is expanded by default, or
  the composer retains submitted text.
- Desktop and narrow viewport screenshots show no overlap or horizontal overflow.

## Risks

- Screenshots can be flaky if timestamps, fonts, or animations are unstable.
  Mitigation: use deterministic fixtures, stable viewports, masked dynamic zones,
  and DOM assertions for critical invariants.

