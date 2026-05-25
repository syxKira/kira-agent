## Context

Stages 01-09 gave Kira a functional local web app with provider selection, streaming events, graph reliability, HITL, skill/project panels, memory, transcript continuity, safety diagnostics, audit, trace, and local smoke coverage. The current frontend has no `web/DESIGN.md`, and `web/src/styles.css` is still a light scaffold with simple panels, a right inspector, a basic timeline, and responsive reflow.

Stage 10 is the final product-experience pass. It must make the existing local web app feel like Kira's intended dark local agent cockpit without changing runtime behavior, adding new providers/tools/skills, or turning the welcome screen into marketing content.

## Goals / Non-Goals

**Goals:**

- Establish `web/DESIGN.md` as the design contract for tokens, layout, timeline mapping, states, responsive behavior, and screenshot acceptance.
- Build a dark, developer-focused single-agent welcome screen with one Kira card and a clear `Start Now` action.
- Refine the workbench into a stable shell with a task rail, centered timeline, assistant identity, bottom composer, event-specific timeline cards, and responsive inspector/drawer behavior.
- Preserve Stage 01-09 semantics for streaming, transcript, hidden thinking, tools, HITL, project knowledge, memory, diagnostics, audit, trace, permissions, and redaction.
- Add focused visual and accessibility smoke checks for the Stage 10 frontend states.

**Non-Goals:**

- No backend runtime, provider, graph, tool, skill, memory, transcript, persistence, or shared schema changes unless an apply task discovers a strictly necessary frontend-facing compatibility fix.
- No multi-agent UI, marketplace, agent switching, cloud/team features, remote auth, theme customization, or mobile-native packaging.
- No code-agent features, project mutation tools, general shell, git/LSP workflows, or hidden thinking shown as answer text.
- No new frontend dependency by default. Any dependency added during apply must be justified in this design and covered by tests.

## Decisions

### 1. Use `web/DESIGN.md` As The UI Source Of Truth

Add a markdown design contract under `web/` before editing components. It will define tokens, layout rules, component states, event-to-UI mapping, do/don't rules, accessibility rules, and screenshot checks.

Rationale: future coding agents need a compact, local source of visual truth. Keeping it in `web/` makes it visible to frontend work without mixing product design rules into runtime specs.

Alternatives considered:

- Rely on the roadmap stage document only: rejected because Stage 10 needs a durable frontend-specific contract after the OpenSpec change is archived.
- Encode the design only in CSS variables: rejected because component behavior, event mapping, and screenshot rules need prose as well as tokens.

### 2. Tokenize The Existing Frontend Into A Neutral Dark Shell

Convert the current light scaffold into CSS variables or an equivalent theme module using neutral dark canvas/surface colors, hairline borders, compact radii, readable text contrast, and restrained blue/green/violet Kira accents.

Rationale: the desired UI is closer to a local IDE or agent cockpit than a SaaS landing page. Tokens also make visual smoke failures easier to fix consistently.

Alternatives considered:

- Keep light mode and polish spacing only: rejected because Stage 10 explicitly requires the dark workbench direction.
- Add a full design-system package: rejected by default because the existing app is small and Stage 10 does not require a dependency.

### 3. Keep Welcome As One Agent, Not A Landing Page

The first viewport will present `Kira Agent`, a concise local-workflow subtitle, one Kira agent card, readiness chips, and `Start Now`. It will not show multiple agents, marketing sections, decorative hero art, or feature-tour content.

Rationale: Kira v0 has one agent. A multi-agent or marketing entry point would misrepresent the product and distract from the local workbench.

Alternatives considered:

- Keep the current centered text panel: rejected because it does not communicate the agent identity or final product direction.
- Add agent choices for future extensibility: rejected because multi-agent UI is explicitly out of scope.

### 4. Compose The Workbench From Stable Frontend Regions

Refactor the workbench presentation around stable regions: task/session rail, main timeline, assistant identity/status row, bottom composer/running controls, and optional inspector/drawer. Existing data-fetching and API calls should stay in place unless small extraction is required to keep components maintainable.

Rationale: the frontend already owns the local web experience. Separating presentation regions makes event-specific UI easier to test without changing backend contracts.

Alternatives considered:

- Build a new route hierarchy: deferred because the app can satisfy Stage 10 within the current Vite/React shell.
- Move inspector state into backend-specific UI models: rejected because Stage 10 is presentation-only and existing API contracts already expose the needed facts.

### 5. Render Timeline Events By Semantics, Not Raw Payload Shape

Map normalized event types to visual treatments:

- `text_delta`: normal assistant answer text.
- `thinking_delta`: subdued or collapsed thinking/status row, never answer text.
- `tool_start`: compact calling row with tool name and scope.
- `tool_result`: bounded expandable card with preview, metadata, and copy control.
- project retrieval/context items: cited snippet cards with stale/omitted/truncated metadata.
- `interrupt`: waiting row plus focused HITL panel.
- `resume`: user decision marker.
- `retry`: compact attempt row.
- `side_effect_reused`: debug-visible reuse marker.
- `checkpoint`: debug-only marker.
- `error`: concise error block with next-action affordance when one already exists.
- cancelled/reconnecting/no-provider-key/done: distinct state rows or composer states.

Rationale: Stage 05-09 already normalized the runtime events. Stage 10 should make those semantics scannable without exposing hidden thinking, raw secrets, or raw internal payloads.

Alternatives considered:

- Render generic JSON blocks for every non-text event: rejected because it hides important state and creates unreadable timelines.
- Hide thinking/tool/debug states entirely: rejected because Kira must remain inspectable as a local agent.

### 6. Treat Responsive And Accessibility Behavior As Acceptance, Not Cleanup

Desktop uses the rail + timeline + inspector/drawer shell. Narrow viewports collapse the rail and inspector while keeping timeline and composer primary. Controls must have accessible names, visible focus states, keyboard paths for run/stop/card expansion/HITL resume, and text wrapping that avoids overlap.

Rationale: Stage 10 is a visual refinement stage, so layout and accessibility regressions are product failures rather than polish tasks.

Alternatives considered:

- Validate responsive behavior only manually: rejected because Stage 10 requires visual smoke checks.
- Make mobile a separate product surface: deferred; this stage only needs usable narrow-web behavior.

## Impact By Area

- Backend: no planned changes. Existing endpoints for runs, resume, transcript, skills, project knowledge, memory, doctor, audit, and trace remain authoritative.
- Frontend: primary implementation area. Changes affect `web/DESIGN.md`, component decomposition, `styles.css` or theme files, tests, fixtures, and smoke coverage.
- Shared contracts: no planned schema changes. Existing normalized events and response types must continue to drive UI.
- Provider config/selection: no behavior changes. UI may display redacted readiness and selected model/profile metadata already exposed by existing APIs.
- Streaming: no event contract changes. UI grouping and presentation must tolerate replay/reconnect and duplicate-safe cursor behavior from previous stages.
- Transcript/context: visible transcript remains separate from hidden thinking, summaries, replacement stubs, and context metadata.
- Persistence: no new migrations or stored UI state required.
- Permissions: existing Stage 09 permission and audit metadata must be shown accurately without adding new decisions.
- Testing: frontend unit tests, DOM-level responsive checks, screenshot/visual smoke checks, keyboard/focus checks, and no-secret/hidden-thinking regressions.

## Risks / Trade-offs

- Visual refactor regresses existing behavior -> Preserve API calls and existing tests while extracting presentation components incrementally.
- Hidden thinking appears as answer text -> Keep event grouping tests and visual smoke assertions that separate `thinking_delta` from `text_delta`.
- Dark tokens reduce contrast -> Record contrast expectations in `web/DESIGN.md` and include accessibility checks for key controls and text.
- Long tool or retrieval output breaks layout -> Use stable card dimensions, internal scroll/expand behavior, and long text fixtures.
- Screenshot checks become brittle -> Keep viewport sizes and fixture content deterministic, and assert high-level layout/overlap rather than pixel-perfect art direction.
- Scope creep into runtime semantics -> Keep backend/shared tasks out of the checklist except for verification that existing contracts still support the UI.

## Migration Plan

1. Add `web/DESIGN.md` and align frontend tokens with the Stage 10 design language.
2. Refactor the welcome screen and workbench shell presentation while preserving existing app flow.
3. Add event-specific timeline and inspector presentation using existing KiraEvent and API data.
4. Add deterministic frontend fixtures for long text, long JSON/tool output, HITL, errors, reconnecting, and no-provider-key states.
5. Add responsive, accessibility, and visual smoke checks, then run frontend test/build and OpenSpec validation.

Rollback strategy: changes are frontend-only by design. Reverting Stage 10 UI files returns the app to the Stage 09 functional scaffold without database migration or backend contract rollback.

## Open Questions

- Should Stage 10 visual smoke use the current Vitest/jsdom stack only, or add a browser screenshot runner during apply if the repo has no existing screenshot mechanism?
- Should the optional inspector default open on desktop, or start collapsed until the user selects diagnostics/project/memory details?
- Which exact fixture names should become the canonical Stage 10 screenshot fixtures after implementation begins?
