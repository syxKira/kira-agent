## Why

Stage 11 fixed concrete frontend defects, but it still leaves Kira too close to
an event workbench. The next frontend work needs a shared contract based on the
more mature cis-mira chat experience before implementation agents start moving
components around. This change creates that contract and makes the dependency
policy explicit.

## Scope

- Add `docs/mira-frontend-study/` with focused notes on layout, streaming,
  reasoning/tools, composer/actions, and Kira target UI.
- Record the cis-mira files that future frontend work should study.
- Define what Kira adopts, adapts, and does not copy from cis-mira.
- Permit small user-experience dependencies when they are stable, useful, and
  isolated behind Kira-owned components.

## Non-Goals

- No UI implementation.
- No backend API or SSE contract changes.
- No direct adoption of cis-mira's large business state, service hooks,
  tracking, multi-agent marketplace, or rich editor stack.
- No removal of Stage 11; this change makes Stage 12-15 the new frontend main
  line after Stage 11.

## Acceptance Criteria

- The study docs exist and name concrete cis-mira source files.
- The docs explain the difference between interaction patterns Kira should copy
  and business dependencies Kira should avoid.
- The docs state that useful UX dependencies may be introduced case-by-case.
- Later OpenSpec changes can cite the Stage 12 study instead of relying on
  screenshots alone.

## Risks

- The study can become vague design prose. Mitigation: require concrete source
  paths, adopted patterns, rejected dependencies, and acceptance invariants.
- The dependency policy can be misread as "never add dependencies." Mitigation:
  explicitly allow small stable UX dependencies when they are justified.

