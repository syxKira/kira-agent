## 1. Design Contract And Theme

- [x] 1.1 Add `web/DESIGN.md` with Stage 10 tokens, type scale, spacing, layout regions, component states, timeline event mapping, responsive rules, accessibility requirements, and screenshot acceptance.
- [x] 1.2 Refactor frontend styling around Kira dark design tokens without adding a dependency unless the implementation documents and tests the reason.
- [x] 1.3 Add or update tests that assert key token-driven classes/states render without exposing provider secrets or hidden thinking as answer text.

## 2. Welcome And Workbench Shell

- [x] 2.1 Redesign `WelcomeScreen` as a dark one-agent Kira launch view with readiness chips and a primary `Start Now` action.
- [x] 2.2 Add the Stage 10 task/session rail with new-task affordance, selected/running/interrupted/completed states, and safe conversation metadata.
- [x] 2.3 Refactor `AgentWorkbench` presentation into stable shell regions for rail, assistant identity, main timeline, composer/running controls, and inspector/drawer.
- [x] 2.4 Add responsive behavior for desktop, tablet, and narrow viewports so rail/inspector collapse without hiding the composer or timeline.

## 3. Timeline, Cards, And Composer

- [x] 3.1 Add event-specific timeline components for visible text, thinking/status, tool start, tool result, retrieval snippet, checkpoint, interrupt, resume, retry, side-effect reuse, error, cancelled, reconnecting, no-provider-key, and done states.
- [x] 3.2 Add bounded tool/retrieval cards with metadata, truncation, internal scroll or expand/collapse behavior, and copy controls.
- [x] 3.3 Polish the composer with model/profile indicator, fixture/auto status, run/stop states, keyboard submit behavior, disabled states, and clear focus styling.
- [x] 3.4 Preserve existing provider auto selection, explicit fixture run, transcript continuity, HITL resume, retry/replay, and no-secret rendering tests.

## 4. Inspector And Supporting Panels

- [x] 4.1 Restyle skill catalog/details, active skill, and workflow context surfaces to fit the dark inspector/drawer without changing skill semantics.
- [x] 4.2 Restyle project knowledge, retrieval citations, stale/omitted/truncated metadata, and context trace surfaces for compact scanning.
- [x] 4.3 Restyle memory, diagnostics doctor, audit, trace, permission, replacement inspection, and safety states using existing APIs and redaction behavior.
- [x] 4.4 Add keyboard and screen-reader labels for inspector tabs, drawer controls, copy buttons, card expanders, and HITL actions.

## 5. Visual And Accessibility Coverage

- [x] 5.1 Add deterministic frontend fixtures for welcome, idle workbench, running timeline, long assistant text, long JSON/tool result, HITL approval/edit/question, error, reconnecting, no-provider-key, and narrow viewport states.
- [x] 5.2 Add visual or screenshot smoke checks for desktop welcome, desktop workbench, running timeline, tool card, HITL, error, long text, and narrow viewport layout.
- [x] 5.3 Add accessibility checks for focus order, accessible names, keyboard-only run/stop/card expansion/HITL resume, contrast-sensitive states, and wrapping within fixed-format UI.
- [x] 5.4 Update `web/README.md` or local smoke docs with Stage 10 visual smoke commands and expected fixture/no-key behavior.

## 6. Validation

- [x] 6.1 Run `pnpm test` from `web/`.
- [x] 6.2 Run `pnpm build` from `web/`.
- [x] 6.3 Run any Stage 10 screenshot or visual smoke command added during apply.
- [x] 6.4 Run `openspec validate stage-10-web-experience-refinement --strict`.
- [x] 6.5 Run `openspec status --change stage-10-web-experience-refinement` and confirm implementation tasks are complete before requesting archive approval.
