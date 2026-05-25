## Context

Stages 01-10 delivered Kira's local runtime, providers, tool protocol, skill-driven graph, HITL, project knowledge, memory, transcript continuity, safety/audit/trace, and the dark Stage 10 workbench shell. During hands-on testing the user reported that the resulting frontend still feels like a developer dashboard rather than a focused local agent chat. Specifically:

- Hidden thinking renders as a permanent visible row above each assistant answer, leaving a long static `Thinking` line that visually competes with the answer instead of behaving like the requested `思考过程` disclosure.
- The assistant answer row has a large vertical white space between the `Assistant` label and the answer text because the row uses block-level `<span>`/`<p>` siblings with default block margins.
- The prompt input retains its previous content after submit, forcing the user to manually clear the box before typing the next prompt.
- The right inspector panel is always rendered with a wall of operator UI: `Conversations` (with select / Create / Refresh / Compact), `Skills`, `Memory`, `Project`, `Context`, `Safety`, plus `Run fixture` / `Run error fixture` / `Run HITL fixture` buttons. This makes the chat surface feel like a control panel rather than a conversation.
- The welcome screen still uses Stage 10 scaffold copy (`Local Web Agent`, `Local agent`, `FastAPI local`, `Read-only context`, `Auto or fixture`) and the welcome panel is left-justified rather than centered.

The user explicitly asked to study `/Users/bytedance/Desktop/code-agent-set/cis-mira` and align Kira's chat experience with its layout (header / scrollable content / footer composer with bounded max width), interaction details (clear input on submit, clean message bubbles, collapsible reasoning blocks, tool activity in the conversation timeline), and tone (focused chat agent rather than operator dashboard). cis-mira is a layout/interaction reference only; we will not import its Slate editor, Allotment, or other heavy dependencies into Kira.

Reference files inspected from cis-mira:

- `src/components/chat-layout/chat-page-ui.tsx` and `chat-page-ui.module.less`: three-section chat page shell, header/content/footer ownership, centered scroll content, and split-view behavior to avoid for Kira's default surface.
- `src/components/chat-layout/chat-footer-ui.tsx`: footer constrained through `AppLayout.MaxWidthLayout`, matching the desired centered composer pattern.
- `src/routes/chat-page/mira-page.tsx`: chat page orchestration, session changes closing third-column surfaces, and a main flow built around header + message list + prompt input.
- `src/routes/chat-page/components/messages/message-list-native-scroller.tsx` and `message-list.module.less`: native scroll controller, centered message list, and bounded message content behavior.
- `src/routes/chat-page/components/messages/message-item/deep-think-shell.tsx`, `deep-think-renderer.tsx`, and `thinking-line-clamp.tsx`: collapsed-by-default reasoning shell and expandable thinking content patterns.
- `src/components/prompt-input/prompt-input.tsx` and `src/hooks/use-chat-manager.ts`: send-path input clearing through `editorRef.current.clearContent()` / `setPromptInputValue("")`.

Stage 11 is a frontend-only refinement that turns the chat surface into the default Kira experience while preserving every Stage 01-10 backend, runtime, and safety contract.

## Goals / Non-Goals

**Goals:**

- Center the welcome screen content (vertically and horizontally) and update copy to a focused single-agent Kira launch view with `一个专业的数据agent助手` positioning, with no `FastAPI local` / `Read-only context` / `Auto or fixture` readiness chips, and a `立刻开始` primary action.
- Make the chat timeline and composer the default workbench experience, removing the always-visible operator inspector, prominent `Inspector` entry point, and the fixture/error/HITL run buttons from the default desktop layout.
- Render hidden thinking as a collapsible `思考过程` block (closed by default) that groups consecutive `thinking_delta` events into one toggleable row.
- Render tool use in the conversation itself as grouped `调用工具` timeline rows/cards, so the user can understand agent action without opening a right inspector.
- Render the assistant answer as a tight chat bubble where label, text, and timestamp belong to one coherent unit with no oversized vertical gap.
- Clear the composer input after a successful submit and keep focus on the input so the next prompt can be typed immediately.
- Align workbench spacing/layout with the cis-mira three-section pattern (header / scrollable timeline / footer composer with bounded max width) without importing cis-mira dependencies.
- Update the rail brand copy from `Local agent` to `一个专业的数据agent助手`.

**Non-Goals:**

- No backend, provider, tool, skill, memory, transcript, audit, trace, or HITL semantic changes.
- No new product frontend dependencies (no Slate editor, no Allotment, no design-system package). A minimal browser-level test dependency is allowed only if existing Vitest/jsdom coverage cannot verify layout-critical behavior.
- No multi-agent UI, marketplace, theme switcher, or mobile-native shell.
- No reintroduction of code-agent capabilities (project mutation, git, LSP, general shell, hidden thinking as answer text).
- No relaxation of Stage 09 redaction, permission, audit, or no-secret guarantees.

## Decisions

### 1. Center And Localize The Welcome Screen Without Readiness Chips

The welcome screen will use a flex/grid container that centers its content both vertically and horizontally. The agent card subtitle becomes `一个专业的数据agent助手`. The `readiness-grid` block (`FastAPI local` / `Read-only context` / `Auto or fixture`) is removed entirely. The primary action label becomes `立刻开始`. The eyebrow / page heading copy stays as `Kira Agent` so the brand identity remains.

Rationale: The user explicitly requested centered welcome content, the new positioning copy, and removal of the readiness chips. The chips never represented user-facing value and confused the agent identity by surfacing backend implementation details.

Alternatives considered:

- Replace the readiness chips with localized equivalents: rejected because the user specifically asked to remove them.
- Keep the readiness data behind a hover/tooltip: rejected because Stage 11 prioritizes a clean welcome and Stage 09 doctor diagnostics already expose readiness elsewhere.

### 2. Make The Chat Surface The Default Workbench

The default desktop workbench will render: task rail (left) + chat surface (center: header + timeline + composer footer). The right-hand operator inspector (Conversations select/Create/Refresh/Compact, Skills, Memory, Project, Context, Safety), the prominent `Inspector` header button, and the `Run fixture` / `Run error fixture` / `Run HITL fixture` buttons will be removed from the default chat surface.

If we keep the underlying React components for future stages, they must be deleted from the default render tree or gated behind an explicit non-default developer/debug affordance such as a debug route or environment flag. Stage 11 prefers removing them from the chat surface entirely; Stage 09 audit/trace and Stage 06-07 skill/memory APIs remain reachable from doctor/trace endpoints and can be re-surfaced in a future stage if needed.

Rationale: The user explicitly said the right-hand panels and fixture buttons must not be visible by default. A chat-first surface aligns Kira with the cis-mira reference layout and the user's stated `数据agent助手` positioning.

Alternatives considered:

- Keep the inspector behind a collapsed drawer reachable from a header button: rejected for the Stage 11 default because even the button keeps the interface framed as an operator dashboard; acceptable only behind a non-default developer/debug mode.
- Move the inspector content to a separate route: deferred; not requested by the user.

### 3. Group Hidden Thinking Into One Collapsible Block (Closed By Default)

Replace the per-event `Thinking` row with a `ThinkingBlock` component that:

- Aggregates consecutive `thinking_delta` events between two visible answer turns into one block.
- Renders as a dim, single-line `<details>`-style row with a `思考过程` label and a chevron toggle, closed by default.
- When opened, shows the joined hidden thinking text in a subdued style, never as answer text and never copied into clipboard answer flows.
- Resets when a new run / new turn starts.

Rationale: The user's screenshots 2 and 3 show the desired collapsible reasoning block (`思考过程`). Closed-by-default also fixes the assistant-row gap because the visible answer no longer sits below a long permanent `Thinking` row.

Alternatives considered:

- Render thinking inline as a faded paragraph: rejected because it still bleeds into the visible answer area and does not match the requested toggle UX.
- Show thinking only in a separate inspector: rejected because some users want quick inline expand without leaving the chat.

### 4. Render Tool Activity Inline In The Timeline

Tool activity will be grouped into a `ToolActivityBlock` (or equivalent) instead of relying on the inspector for understanding execution. The UI should:

- Render `tool_start` as a compact `调用工具` row with tool name, status, and optional scope metadata.
- Merge the matching `tool_result` into the same logical block when correlation metadata is available; otherwise render a neighboring result card without changing event order.
- Use an expandable preview for JSON/text result payloads, bounded height, copy affordance, and stable word wrapping.
- Keep tool output visually distinct from assistant answer text and hidden thinking.

Rationale: The user's reference image shows agent work as part of the conversation: reasoning rows, tool invocation rows, and bounded result previews. If tool details only live in the right inspector, the chat surface cannot demonstrate the agent's capabilities.

Alternatives considered:

- Leave tool events as raw status cards: rejected because it preserves the current dashboard feel and does not match the requested "思考和使用工具" experience.
- Put all tool payloads inline expanded by default: rejected because large JSON/tool output would dominate the conversation and hurt readability.

### 5. Tighten The Assistant Answer Row Into A Chat Bubble

Refactor the answer row from `<article><span>Assistant</span><p>{text}</p><time/></article>` (block-level siblings with default margins) into a chat bubble where the label is a small caption above (or inline with) a single content block, with margins controlled by the bubble container rather than default `p` block spacing. Apply the same pattern to the user prompt row so chat layout is symmetric.

Rationale: The user reported a "very strange empty space" between the `Assistant` label and the answer text. The current CSS lets the `<p>` element inherit large default block spacing inside the `.timeline-row` flex/grid. A chat bubble container with controlled padding/gap removes the gap.

Alternatives considered:

- Tweak only the `margin-bottom` on `.event-type`: rejected because the symptom is a consequence of broader row layout, and a small CSS tweak is fragile across long answers, code blocks, and timestamps.
- Use a third-party chat bubble library: rejected to keep dependencies stable.

### 6. Clear Composer Input After Submit And Keep Focus

In `submitPrompt` (and any HITL/resume flow that owns the composer), after successfully starting the run we will call `setPrompt("")` and re-focus the composer input. We will keep `prompt` as React-controlled state but no longer seed it with `Ask the configured model a question` after submit. The initial placeholder text remains, but the value defaults to empty string.

Rationale: The user explicitly asked for the input to clear after each conversation. cis-mira's `editorRef.current?.clearContent()` in `handleOnSendMessage` is the standard pattern.

Alternatives considered:

- Auto-clear on stream `done`: rejected because the user wants the box cleared the moment the prompt is dispatched, not after the model finishes streaming.
- Replace the `<input>` with a contenteditable editor like Slate: rejected to avoid a heavy dependency and to keep the change minimal.

### 7. Align Layout With cis-mira's Three-Section Chat Pattern

Restructure the workbench main column into a three-section flexbox: (1) sticky agent header, (2) scrollable timeline, (3) sticky composer footer; with a bounded max width on the timeline and composer (matching cis-mira's `MaxWidthLayout` idea). The task rail keeps its existing fixed left column.

Rationale: cis-mira's chat layout is the explicit reference. A bounded max-width and centered chat region produces the calm focused chat surface the user wants.

Alternatives considered:

- Full-width chat: rejected because long messages without max-width make code/text harder to read.
- Adopt cis-mira directly as a workspace package: rejected; we mirror layout patterns only.

## Risks / Trade-offs

- [Risk] Removing operator panels from the default chat surface may surprise developers who relied on them. → Mitigation: doctor/audit/trace APIs remain unchanged; a follow-up stage can reintroduce a focused inspector if needed.
- [Risk] Collapsed-by-default thinking could be misread as hiding agent behavior. → Mitigation: keep a clear `思考过程` row that toggles open with one click; preserve Stage 09 audit/trace exposure unchanged.
- [Risk] Tool result previews can become noisy or leak raw debug payloads. → Mitigation: reuse Stage 09 frontend-safe redaction/output bounds and default large payloads to collapsed previews.
- [Risk] Layout refactor could regress responsive behavior. → Mitigation: keep Stage 10 narrow-viewport rules and add tests that confirm timeline + composer remain reachable at narrow widths after the refactor.
- [Risk] Clearing the composer after submit removes the last prompt as a quick re-edit affordance. → Mitigation: the timeline already shows the user's prompt as a chat bubble immediately after submit, providing context for the next message.
- [Risk] cis-mira layout reference could leak heavier patterns. → Mitigation: only mirror layout/spacing/interaction shape, not the dependency stack.
- [Risk] Stage 11 changes may conflict with future Stage N inspector reintroduction. → Mitigation: keep underlying APIs and components in source where reasonable, but never render them from the default chat surface; explicitly document this contract in `web/DESIGN.md`.

## Migration Plan

1. Record the cis-mira reference notes in `web/DESIGN.md` before implementation so the apply stage has a visible design source of truth.
2. Update `WelcomeScreen.tsx` copy and centering; remove the `readiness-grid` block; change the primary action to `立刻开始`; update the rail brand copy in `AgentWorkbench.tsx`.
3. Refactor the workbench shell so the right inspector, prominent inspector button, and fixture buttons are no longer rendered by default; remove or relocate the `inspector` aside, the operator panels, and the fixture buttons from the default chat surface.
4. Introduce a `ThinkingBlock` (or equivalent grouped collapsible) for `thinking_delta` events, default-closed and labeled `思考过程`.
5. Introduce a grouped `ToolActivityBlock` (or equivalent) for `tool_start` / `tool_result` events with bounded expandable previews.
6. Refactor the assistant answer row and user prompt row into chat-bubble layouts with controlled spacing.
7. Update `submitPrompt` to clear the prompt input after creating the run and re-focus the input.
8. Update `styles.css` to apply cis-mira-style three-section layout with bounded max width and centered chat region.
9. Update or replace tests that asserted the operator panels, lingering prompt, or always-visible thinking row; add new tests for the chat-first defaults, collapse behavior, tool activity grouping, bubble spacing, and composer clear-on-submit.
10. Run `pnpm typecheck`, `pnpm test`, `pnpm build`, and `openspec validate stage-11-frontend-chat-experience --type change --strict`.

Rollback strategy: Stage 11 is frontend-only by design. Reverting the Stage 11 patches returns the app to the Stage 10 surface without database migration or backend rollback.

## Open Questions

- None for Stage 11. The agreed default is: exact product copy `一个专业的数据agent助手`, primary action `立刻开始`, `思考过程` as the visible reasoning label, and no default right-side inspector/operator surface.
