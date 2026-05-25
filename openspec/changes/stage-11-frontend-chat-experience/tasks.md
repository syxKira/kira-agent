## 0. cis-mira Reference Audit

- [x] 0.1 Inspect and summarize the relevant cis-mira frontend patterns in `web/DESIGN.md` before UI edits: `chat-page-ui`, `chat-footer-ui`, message list scroller, `deep-think-shell`, `deep-think-renderer`, `thinking-line-clamp`, `prompt-input`, and `use-chat-manager`.
- [x] 0.2 Record which cis-mira patterns are adopted and which are explicitly not adopted (Slate editor, Allotment split view, design-system dependency, multi-agent selection).

## 1. Welcome Screen Refinement

- [x] 1.1 Update `web/src/components/WelcomeScreen.tsx` agent card subtitle from `General local project agent` to `一个专业的数据agent助手`.
- [x] 1.2 Remove the `readiness-grid` block (`FastAPI local`, `Read-only context`, `Auto or fixture`) from `web/src/components/WelcomeScreen.tsx` and any associated CSS that only existed to support it.
- [x] 1.3 Change the primary welcome action label to `立刻开始` and remove product-facing `Local Web Agent` / `Local agent` scaffold copy from the first viewport.
- [x] 1.4 Adjust `welcome-shell` and `welcome-panel` rules in `web/src/styles.css` so the welcome content centers both vertically and horizontally at desktop and narrow widths without depending on the removed readiness chips.
- [x] 1.5 Add or update tests in `web/src/__tests__/` (or existing welcome tests) that assert the welcome screen shows the new agent description, shows `立刻开始`, does not show `FastAPI local` / `Read-only context` / `Auto or fixture`, and renders centered.

## 2. Workbench Chat-First Default

- [x] 2.1 Update the rail brand copy in `web/src/components/AgentWorkbench.tsx` from `Local agent` to `一个专业的数据agent助手` (the agreed phrasing recorded in `web/DESIGN.md`).
- [x] 2.2 Remove the right-hand `inspector` aside from the default workbench layout in `web/src/components/AgentWorkbench.tsx`, including the `Run fixture` / `Run error fixture` / `Run HITL fixture` buttons and the `ConversationPanel`, `SkillPanel`, `MemoryPanel`, `ProjectPanel`, `ContextInspector`, and `SafetyPanel` from the default render.
- [x] 2.3 Remove the prominent default `Inspector` header button. If an inspector/debug UI is retained, gate it behind an explicit non-default developer/debug affordance such as a debug route or environment flag.
- [x] 2.4 Update the workbench grid in `web/src/styles.css` to a chat-first layout (rail + chat surface) without the inspector column at desktop widths, while preserving narrow-viewport behavior so the timeline and composer remain reachable.
- [x] 2.5 Restructure the workbench main column into a sticky agent header + scrollable timeline + sticky composer footer with a bounded max width that matches the cis-mira three-section chat pattern.
- [x] 2.6 Add or update tests that assert the default workbench does not render the operator panels, fixture buttons, or prominent inspector entry point and that the chat surface (timeline + composer) is reachable.

## 3. Collapsible Thinking Block

- [x] 3.1 Add a `ThinkingBlock` component (or equivalent grouped collapsible) under `web/src/components/` that aggregates consecutive `thinking_delta` events between visible answer turns into one collapsible row, rendered with a `思考过程` label, a chevron toggle, and closed by default.
- [x] 3.2 Update the timeline render path in `web/src/components/AgentWorkbench.tsx` so `thinking_delta` events feed into the new `ThinkingBlock` instead of producing per-event always-visible rows.
- [x] 3.3 Ensure the collapsible thinking content remains visually subdued, never duplicates into `text_delta` answer text, and does not get copied by any answer copy control.
- [x] 3.4 Add tests that assert: `思考过程` rows default to collapsed, the toggle opens/closes the row, hidden thinking text is not merged into the answer bubble, and a new run/turn resets the block.

## 4. Tool Activity Timeline

- [x] 4.1 Add a `ToolActivityBlock` component (or equivalent grouped renderer) for `tool_start` / `tool_result` events with a compact `调用工具` header, tool name, status, timestamp, and optional scope metadata.
- [x] 4.2 Group a matching `tool_result` with its `tool_start` when event metadata allows; otherwise render the result as an adjacent card without reordering timeline events.
- [x] 4.3 Render long JSON/text tool results in bounded expandable previews with stable wrapping and copy controls, reusing existing redaction/bounded-output safeguards.
- [x] 4.4 Add tests that assert tool start/result grouping, collapsed long preview behavior, and that tool output does not merge into assistant answer text.

## 5. Assistant And User Message Bubble Spacing

- [x] 5.1 Refactor the assistant answer row in `web/src/components/AgentWorkbench.tsx` into a chat-bubble layout where the `Assistant` label, the answer text, and the timestamp share one tightly spaced bubble container.
- [x] 5.2 Apply a symmetric chat-bubble layout to the user prompt row (and transcript user message rows) so user/assistant rows have consistent spacing.
- [x] 5.3 Update `web/src/styles.css` to remove the oversized vertical gap between the message label and the message text by controlling spacing on the bubble container instead of relying on default `<p>` block margins.
- [x] 5.4 Add tests that assert no large vertical gap exists between the `Assistant` label and the answer text in a rendered answer row, and that the bubble layout applies to both user and assistant rows.

## 6. Composer Clear-On-Submit

- [x] 6.1 Update `submitPrompt` (and any HITL/resume composer flow) in `web/src/components/AgentWorkbench.tsx` so that after the run is successfully created the prompt input value is cleared and focus stays on the input.
- [x] 6.2 Replace the seeded initial prompt `Ask the configured model a question` with an empty string, keeping the placeholder text on the input.
- [x] 6.3 Add tests that assert: submitting a prompt clears the input value, the input keeps focus, and the next prompt can be typed without manual clearing.

## 7. Layout Polish Inspired By cis-mira

- [x] 7.1 Apply a bounded max-width container around the timeline and composer so the chat surface stays centered horizontally at wide viewports.
- [x] 7.2 Make the agent header sticky to the top of the chat surface and the composer sticky to the bottom, with the timeline scrolling between them.
- [x] 7.3 Verify narrow-viewport behavior so the rail and chat surface still cooperate without horizontal overflow.
- [x] 7.4 Update or add `web/DESIGN.md` Stage 11 entries that record the new chat-first layout, the exact product copy, and the cis-mira reference files used.

## 8. Validation

- [x] 8.1 Run `pnpm typecheck` from `web/`.
- [x] 8.2 Run `pnpm test` from `web/`.
- [x] 8.3 Run `pnpm build` from `web/`.
- [x] 8.4 Manually verify the welcome screen, chat surface, `思考过程` collapse, tool activity grouping, assistant row spacing, and composer clear-on-submit at desktop and narrow widths.
- [x] 8.5 Add a browser-level screenshot smoke check if Vitest/jsdom cannot verify the centered welcome, sticky composer, or absence of right inspector visually.
- [x] 8.6 Run `openspec validate stage-11-frontend-chat-experience --type change --strict` and confirm the change passes.
- [x] 8.7 Run `openspec status --change stage-11-frontend-chat-experience` and confirm tasks are complete before requesting archive approval.
