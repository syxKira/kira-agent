## Why

Stage 10 shipped the dark Kira workbench shell, but real hands-on use surfaced concrete UX defects that make the local agent feel unfinished and unfocused: hidden thinking renders as a permanent always-on row above the answer, the assistant answer row leaves a large vertical gap between its `Assistant` label and the actual text, the prompt input keeps its previous content after submission, the right-hand inspector exposes a wall of operator panels (Conversations, Skills, Memory, Project, Context, Safety) plus fixture/error/HITL run buttons that overwhelm a chat-first user, and the welcome screen still uses English scaffold copy (`Local agent`, `FastAPI local`, `Read-only context`, `Auto or fixture`) that misrepresents Kira as a generic backend status board. Stage 11 turns the frontend into a focused, chat-first local agent surface aligned with the cis-mira reference layout (`/Users/bytedance/Desktop/code-agent-set/cis-mira`) and the user's stated `一个专业的数据agent助手` positioning, without changing any runtime, provider, tool, skill, memory, transcript, or safety contract from Stages 01-10.

## Scope

- Replace the welcome screen copy with `一个专业的数据agent助手` positioning, remove `FastAPI local` / `Read-only context` / `Auto or fixture` readiness chips, make the primary entry action read `立刻开始`, and center the welcome content vertically and horizontally so the entry experience matches the user's expected look.
- Reduce the workbench right-hand inspector to a chat-first focused area, removing the always-visible `Conversations` / `Skills` / `Memory` / `Project` / `Context` / `Safety` operator panels, prominent `Inspector` entry point, and the `Run fixture` / `Run error fixture` / `Run HITL fixture` buttons from the default chat surface.
- Render hidden thinking as a collapsible/expandable `思考过程` block (closed by default) so it never produces a permanent vertical gap above the assistant answer and matches the cis-mira reasoning block UX.
- Render tool activity as first-class timeline content: group `tool_start` / `tool_result` into compact `调用工具` rows and expandable result cards with tool name, status, bounded JSON/text preview, copy affordance, and stable spacing.
- Fix the empty-gap defect between the `Assistant` label and the assistant answer text by rebuilding the answer row into a tight chat bubble container similar to the cis-mira message layout.
- Clear the prompt composer input after a successful submit, mirroring the cis-mira `editorRef.clearContent()` behavior, and re-focus the input so the next prompt can be typed immediately.
- Align the chat surface (sticky agent header / scrollable timeline / sticky bottom composer with bounded max-width) with the cis-mira `chat-page-ui` three-section layout.
- Update the rail brand copy from `Local agent` to `一个专业的数据agent助手`.
- Add focused frontend tests for: `思考过程` collapse default-closed and toggle, tool activity grouping, assistant row spacing, composer input cleared after submit, welcome content centered without removed chips, and chat-first inspector default state.

## Non-Goals

- No changes to backend APIs, SSE event contracts, provider selection, tool protocol, skill discovery, project knowledge, memory, transcript, audit, trace, or HITL semantics.
- No introduction of marketing-style hero art, multi-agent selection, agent marketplace, theme switcher, mobile-native shell, or remote auth.
- No new design system dependency, Slate editor, Allotment split-view, or other large frontend framework imports beyond what the app already depends on. cis-mira is a layout/interaction reference, not a code dependency.
- No new operator dashboards, no always-visible debug/inspector rail in the default chat experience, and no replacement code-agent features (project mutation, git, LSP, general shell, hidden-thinking-as-answer). Existing diagnostics/trace/audit APIs may remain reachable through an explicit non-default developer/debug affordance if needed.
- No reintroduction of Stage 09 redaction, permission, audit, or no-secret weakening; all safety boundaries stay as-is.

## What Changes

- Restate the welcome screen as a centered, dark, single-agent Kira launch view with `一个专业的数据agent助手` agent description, no readiness chips, and a `立刻开始` primary action.
- Reshape the workbench shell so the chat surface (sticky header + scrollable timeline + sticky composer) is the default focus, removing the operator inspector and prominent `Inspector` control from the default desktop layout while preserving Stage 10 minimal status surfaces (run status, provider label, stop control).
- Introduce a collapsible `ThinkingBlock` component: groups consecutive `thinking_delta` events into one collapsible `思考过程` row, closed by default, with a clear toggle, and never bleeds into the visible assistant answer or copy flows.
- Introduce grouped tool activity rows/cards: `tool_start` shows a compact in-progress row, `tool_result` completes the same logical block when correlation metadata exists, and long result payloads render inside bounded expandable previews.
- Rework the assistant answer row so the label, text, and timestamp share a single tight bubble layout without a vertical white-space gap; apply matching treatment to the user prompt row for layout symmetry.
- Clear the composer input value after a successful submit and keep keyboard focus on the input.
- Adjust workbench CSS grid/spacing so the timeline and composer center horizontally with a bounded max width matching cis-mira's `MaxWidthLayout` pattern, and the composer footer stays sticky to the bottom without overlapping the timeline.
- Update or remove tests/fixtures that asserted the operator inspector, lingering composer text, or always-visible thinking row, and add tests that lock in the new behavior.

## Acceptance Criteria

- The welcome screen shows a centered Kira card with `一个专业的数据agent助手` description, no `FastAPI local` / `Read-only context` / `Auto or fixture` chips, and a single primary `立刻开始` control; the welcome content is vertically and horizontally centered at desktop and narrow widths.
- The workbench default desktop layout shows the task rail, the chat timeline, and the composer footer, and does NOT show the `Conversations` / `Skills` / `Memory` / `Project` / `Context` / `Safety` operator panels, a prominent `Inspector` entry point, or the `Run fixture` / `Run error fixture` / `Run HITL fixture` buttons by default.
- Hidden thinking renders as one collapsible `思考过程` block per run segment, defaults to collapsed, exposes a clear toggle (button or `<details>` summary), and never appears as normal assistant answer text or as a permanent always-visible row.
- Tool activity renders inline in the timeline as grouped `调用工具` rows/cards with status, tool name, bounded preview, and expand/collapse behavior; tool results do not force the user into a right inspector to understand what happened.
- The assistant answer row has no large empty gap between its label and its text; label + text + timestamp render as one coherent message bubble at desktop and narrow widths; the user prompt row uses a symmetric bubble layout.
- After submitting a prompt the composer input value becomes empty, focus stays on the input, and the next prompt can be typed without manually clearing prior text.
- The rail brand copy reads `一个专业的数据agent助手` instead of `Local agent`.
- Stage 01-10 runtime tests, transcript continuity tests, HITL tests, no-secret rendering tests, and provider auto/fixture tests continue to pass; the chat-first changes do not regress streaming, replay, audit, or safety behavior.

## Risks

- Removing the operator inspector from the default chat surface could hide useful data; mitigate by keeping the underlying APIs reachable through doctor/audit/trace endpoints and, if retained, gating UI access behind an explicit non-default developer/debug affordance.
- Collapsing thinking by default could be perceived as hiding agent behavior; mitigate by keeping a clear `思考过程` row that toggles open with one click and leaving Stage 09 audit/trace surfaces unchanged so power users still have full inspectability.
- Welcome copy changes can drift from product intent; lock the agreed phrasing in `web/DESIGN.md` so future stages do not silently regress.
- cis-mira-inspired layout could pull in unintended dependencies; only mirror the layout/spacing/interaction shape, not the underlying framework or editor stack.
- Test fixtures that asserted the previous defects will need careful replacement to avoid losing safety regressions.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `local-web-workbench`: welcome copy, welcome centering, removed readiness chips, `立刻开始` action, chat-first workbench default, removed default operator inspector, composer clear-on-submit and refocus, rail brand copy.
- `timeline-hitl-ui`: collapsible `思考过程` row default-closed, grouped tool activity rows/cards, assistant answer row spacing fix, layout symmetry between user and assistant rows.
- `skill-and-project-ui`: operator panels (skills, project knowledge, memory, context, safety) are no longer rendered by default in the chat surface; if retained at all, they are reachable only behind an explicit non-default inspector or developer affordance.

## Impact

- Frontend: `web/src/components/WelcomeScreen.tsx`, `web/src/components/AgentWorkbench.tsx`, `web/src/styles.css`, related component tests, optional new sub-components for `ThinkingBlock`, `ToolActivityBlock`, and `MessageBubble`, and `web/DESIGN.md` updates.
- Backend: no required behavior changes; existing run, resume, transcript, conversation, skill, project, memory, doctor, audit, trace endpoints stay authoritative.
- Shared contracts: no schema changes; existing `KiraEvent` and transcript shapes remain authoritative.
- Persistence: no migrations.
- Permissions and safety: Stage 09 redaction, permission, audit, no-secret, and hidden-thinking separation remain unchanged.
- Testing: frontend unit/DOM tests for welcome centering, `思考过程` collapse default and toggle, grouped tool activity, assistant row spacing, composer clear-on-submit, and chat-first inspector default; existing Stage 01-10 tests continue to run.
