## Why

Kira has the runtime, safety, persistence, transcript, retrieval, memory, diagnostics, and smoke foundations needed for local use, but the web UI still reads as a light functional scaffold. Stage 10 turns that surface into the intended polished local agent workspace while preserving the runtime and safety contracts already built in Stages 01-09.

## Scope

- Add `web/DESIGN.md` as the frontend design contract for future UI work.
- Redesign the first viewport into a dark single-agent Kira welcome screen with readiness chips and a clear `Start Now` path.
- Refine the workbench into a dark local-agent cockpit with a left task rail, centered timeline, assistant identity, bottom composer, optional inspector/drawer, and stable run-state surfaces.
- Make timeline events visually distinct for visible assistant text, hidden thinking/status, tool start/result, retrieval snippets, HITL interrupts/resumes, retries, reused side effects, checkpoints, errors, cancelled runs, and done states.
- Polish skill, project knowledge, memory, diagnostics, audit, and trace panels so they fit the Stage 10 shell without changing their underlying semantics.
- Add desktop and narrow-viewport visual smoke coverage for welcome, running timeline, tool cards, HITL, error, long text, and no-provider-key/fallback states.

## Non-goals

- No new runtime, provider, tool, skill, memory, transcript, storage, or graph semantics.
- No multi-agent selection UI, marketplace-style agent catalog, or sub-agent orchestration.
- No marketing landing page, decorative illustration-heavy hero, or content-focused homepage.
- No project file mutation, patching, git, LSP, general shell, or code-agent profile.
- No hidden-thinking-as-answer rendering and no weakening of redaction, audit, permission, or provider-secret boundaries.
- No future-stage theme customization, cloud deployment, remote auth, team approvals, or mobile-native packaging.

## What Changes

- Add a Stage 10 frontend design contract that captures color tokens, typography, spacing, layout rules, timeline mapping, component states, responsive behavior, accessibility rules, and screenshot acceptance checks.
- Replace the current welcome scaffold with a dark one-agent launch view for `Kira Agent`, including one Kira card, readiness chips, provider/project/fixture status, and the primary `Start Now` action.
- Replace the current workbench scaffold with a tokenized dark app shell: task/session rail, main timeline, Kira identity row, bottom composer, status controls, and responsive inspector/drawer behavior.
- Add event-specific timeline presentation for thinking/status rows, tool start/result cards, retrieval snippets, HITL rows/panels, retry/reuse/checkpoint/debug markers, error/cancelled/reconnecting states, and done markers.
- Improve long-output behavior with bounded tool/retrieval previews, internal scrolling or expansion, copy affordances, metadata rows, and text wrapping that avoids overlap.
- Add visual smoke and accessibility checks for the Stage 10 shell without requiring real provider keys or network access by default.

## Acceptance Criteria

- `web/DESIGN.md` exists and is specific enough for future frontend edits to follow without relying on screenshots alone.
- The welcome screen shows exactly one Kira agent card and a primary `Start Now` action in a dark, developer-focused first viewport.
- The workbench displays a left task rail, centered timeline, assistant identity, event-specific cards/rows, bottom composer, and inspector/drawer behavior without overlapping text at desktop or narrow widths.
- Hidden thinking remains visually subdued or collapsed and never appears as normal assistant answer text.
- Tool, retrieval, HITL, retry, reused side-effect, error, cancelled, reconnecting, no-provider-key, and done states are distinguishable and keyboard reachable.
- Visual smoke checks cover desktop and narrow viewports, long text, long JSON/tool output, HITL, errors, and fixture/no-key paths.

## Risks

- Visual polish could accidentally change runtime semantics or API shapes; keep Stage 10 limited to frontend presentation, fixtures, tests, and docs unless an existing API already supports the state.
- A dark redesign could reduce readability or contrast; encode tokens and accessibility checks in `web/DESIGN.md` and visual smoke tests.
- New component structure could regress existing Stage 01-09 flows; keep tests around provider auto selection, fixture runs, transcript continuity, HITL, project/skill/memory inspectors, audit/trace, and no-secret rendering.
- Screenshot checks can become brittle; use them for high-level layout and overlap regressions, with deterministic fixture data and stable viewport sizes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `local-web-workbench`: Stage 10 design contract, one-agent welcome, dark workbench shell, task rail, composer polish, responsive layout, and visual state presentation.
- `timeline-hitl-ui`: Event-specific timeline cards/rows, hidden-thinking presentation, tool/retrieval output affordances, HITL visual polish, and retry/error/reuse state mapping.
- `skill-and-project-ui`: Dark inspector/drawer presentation for skills, project knowledge, context, memory, diagnostics, audit, and trace surfaces without changing data semantics.
- `local-packaging-smoke`: Stage 10 visual and accessibility smoke checks for the local web experience.

## Impact

- Frontend: `web/DESIGN.md`, React component structure, CSS/theme tokens, welcome/workbench layout, timeline cards, composer, task rail, inspector/drawer, frontend tests, and smoke fixtures.
- Backend: no required behavior changes; existing fixture, doctor, trace, audit, transcript, project, memory, HITL, and provider-status APIs remain the data sources.
- Shared contracts: no schema changes planned; existing KiraEvent, transcript, context, diagnostics, audit, trace, project, skill, and memory contracts remain authoritative.
- Persistence: no new tables or migrations.
- Permissions and safety: existing Stage 09 redaction, permission, audit, and no-secret rules remain unchanged and must be reflected accurately in UI states.
- Testing: frontend unit tests, responsive DOM checks, screenshot/visual smoke checks, keyboard/focus checks, and existing OpenSpec validation.
