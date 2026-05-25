# Stage 10: Web Experience Refinement

## Goal

Turn Kira's functional web app into a polished local agent workspace: a dark, developer-focused welcome screen with one Kira agent card and a clear "Start Now" action, plus a production-quality chat/workbench layout that makes agent thinking, tool use, file retrieval, HITL, retries, and run state easy to scan.

## Why This Stage

Stages 01-09 make Kira capable, reliable, continuous, and inspectable. This stage makes Kira feel like a finished local web agent. It is intentionally last so core runtime, provider selection, tools, graph reliability, skills, retrieval, memory, transcript continuity, audit, and diagnostics are already stable before visual polish and interaction design become the focus.

The visual direction should follow the user's two references:

- a dark agent workbench with a left task rail, centered conversation timeline, visible assistant identity, thought/tool rows, tool result cards, and a bottom composer;
- a dark welcome screen with a single Kira agent card and a prominent "Start Now" button.

It should also use the `DESIGN.md` approach popularized by `awesome-design-md`: capture tokens, layout rules, component states, do/don't rules, and responsive behavior in a design document that coding agents can follow consistently.

## Scope

- Add a Kira web `DESIGN.md` or equivalent design contract for the frontend.
- Redesign the welcome screen into a single-agent launch view.
- Redesign the workbench into a dark local-agent cockpit:
  - left task/session rail;
  - main conversation timeline;
  - assistant identity row;
  - thinking/status rows;
  - tool start/result cards;
  - project/file retrieval snippets;
  - HITL interrupt rows;
  - retry/error/reused-side-effect markers;
  - bottom composer with model/profile indicator and action controls.
- Create a compact visual language: neutral dark surfaces, hairline borders, restrained Kira accents, clear text hierarchy, and mono snippets for code/tool output.
- Make timeline events visually distinct without exposing hidden thinking as answer text.
- Add empty, loading, running, paused, error, cancelled, completed, reconnecting, and no-provider-key states.
- Add responsive desktop/tablet/mobile layouts.
- Add keyboard-accessible controls and focus states.
- Add screenshot/visual smoke tests for welcome, running timeline, tool card, HITL, error, narrow viewport, and long text.

Excluded:

- New core runtime capabilities.
- New provider/tool/skill/memory semantics.
- Multi-agent selection UI. Kira v0 has one agent card only.
- Marketing landing page content.
- Decorative illustration-heavy hero pages.

## Inputs And Dependencies

- Stage 01 welcome/workbench shell and SSE fixture run.
- Stage 05 event semantics for text, thinking, tool, checkpoint, interrupt, resume, done, and error.
- Stage 06 skill/project knowledge panels and ContextItem trace.
- Stage 07 memory inspector.
- Stage 08 conversation transcript and context continuity.
- Stage 09 doctor, audit, trace, and frontend smoke coverage.
- User-provided screenshots for desired welcome/workbench direction.
- `awesome-design-md` repository and its DESIGN.md pattern.

## Design

### Design Language

Kira should use a dark, technical, calm interface rather than a marketing page. The target mood is closer to a local IDE or agent cockpit than a SaaS homepage.

Recommended tokens:

| Token | Value | Use |
| --- | --- | --- |
| `canvas` | `#151718` | app background |
| `surface` | `#1d2023` | sidebar and composer surface |
| `surfaceRaised` | `#25282c` | selected task, cards, message bubbles |
| `border` | `#363a40` | hairline borders |
| `text` | `#f2f4f7` | primary text |
| `muted` | `#9ca3af` | metadata and secondary text |
| `accentBlue` | `#3b82f6` | user identity, selected state |
| `accentGreen` | `#20e58a` | run/ready/primary action |
| `accentViolet` | `#a78bfa` | Kira agent badge |
| `danger` | `#f97373` | errors |
| `radiusSm` | `6px` | inputs/buttons |
| `radiusMd` | `8px` | cards/panels |
| `fontSans` | `Inter, system-ui, sans-serif` | UI text |
| `fontMono` | `SFMono-Regular, Menlo, Monaco, Consolas, monospace` | code/tool snippets |

Use accents sparingly. The interface should read as neutral dark with small blue/green/violet signals, not as a one-color theme.

### Welcome Screen

The first view has one central launch surface:

- headline: `Kira Agent`;
- concise subtitle for local project workflows;
- one Kira agent card with icon, name, short role, and three capability bullets;
- readiness chips for provider, project root, and fixture/real model status;
- primary `Start Now` button;
- optional secondary `Open Settings` only after provider settings exist.

The page should not show two agent choices. Kira v0 has exactly one agent.

### Workbench

Desktop layout:

| Region | Behavior |
| --- | --- |
| Left rail | New task button, task/session list, status/time metadata |
| Main timeline | User messages on the right, assistant/thought/tool content on the left/center |
| Bottom composer | fixed input area with Kira label, model selector, attachment/context buttons, stop/run controls |
| Optional inspector drawer | skills, tools, project knowledge, memory, state, audit, trace |

Timeline block rules:

| Event | UI Treatment |
| --- | --- |
| `text_delta` | assistant answer text, grouped into readable paragraphs |
| `thinking_delta` | collapsed or subdued "Thinking" row, never normal answer text |
| `tool_start` | slim status line with tool name and scope |
| `tool_result` | expandable card with JSON/text preview, copy button, line/path metadata |
| `checkpoint` | debug-only marker |
| `interrupt` | prominent waiting row plus focused HITL panel |
| `resume` | user decision marker |
| `retry` | compact attempt row |
| `side_effect_reused` | debug-visible reuse marker |
| `error` | concise error block with retry/resume/inspect affordance |
| `done` | completed state and idle composer |

### DESIGN.md Contract

The frontend should include a `DESIGN.md` that future agents read before editing UI. It should capture:

- theme and atmosphere;
- color tokens;
- type scale;
- spacing and layout grid;
- component states;
- timeline event mapping;
- welcome/workbench do's and don'ts;
- responsive behavior;
- screenshot acceptance checklist.

This mirrors the `awesome-design-md` pattern where a markdown design system gives coding agents the visual rules needed to generate consistent UI.

## Implementation Tasks

1. Add `web/DESIGN.md` with Kira design tokens, layout rules, component rules, event mapping, and responsive rules.
2. Refactor frontend styles into tokenized CSS variables or theme module.
3. Redesign `WelcomeScreen` into the one-agent Kira launch screen with `Start Now`.
4. Add task/session rail component and selected/running/interrupted/completed task states.
5. Refactor `AgentWorkbench` into app shell, timeline, composer, and optional inspector/drawer components.
6. Add event-specific timeline components for thinking, tool start/result, interrupt, retry, error, done, and text.
7. Add tool result card affordances: copy, expand/collapse, path/line metadata, JSON/text preview.
8. Add composer controls: model/profile indicator, context buttons, stop/run states, keyboard submit behavior.
9. Add responsive layout for narrow screens: rail collapses, inspector becomes drawer, composer stays usable.
10. Add frontend fixture stories or test fixtures for long text, long JSON, multiple tool cards, HITL, reconnecting, and no-key fallback.
11. Add visual/screenshot smoke tests for desktop and mobile.
12. Add accessibility checks for focus order, labels, keyboard controls, contrast, and text wrapping.

## Validation

- Welcome screen matches the single-agent launch intent and has a clear `Start Now` path.
- Workbench renders task rail, timeline, assistant identity, tool cards, thought/status rows, and composer without overlapping text.
- Hidden thinking never appears as normal assistant answer text.
- Tool cards handle large JSON/text with truncation, internal scrolling, and expand/collapse.
- HITL, error, reconnecting, no-key fallback, and cancelled states are visually distinct.
- Desktop and narrow viewport screenshots pass layout checks.
- Keyboard-only interaction can start a run, submit a prompt, stop a run, expand a card, and resume an interrupt.

## Exit Criteria

- Kira's frontend feels like a coherent local Web Agent product rather than a functional scaffold.
- Future UI implementation has a stable `DESIGN.md` contract to follow.
- The UI remains faithful to runtime safety: no secret leakage, no hidden thinking as answer text, no misleading tool execution states.

## Deferred Work

- Multiple agents, marketplace-style agent selection, theme customization, and mobile-native packaging are future product decisions.
