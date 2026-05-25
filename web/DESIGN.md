# Kira Web Design

## Design Intent

Kira is a local data-agent assistant for project workflows. Stage 10/11 used a dark cockpit as the first polished shell, but Stage 12-15 supersede the default product direction with a cis-mira-informed, light, conversation-first chat experience. It is not a marketing page, an agent marketplace, or a code-agent shell.

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| `--canvas` | `#f3eee5` | app background |
| `--canvas-elevated` | `#f8f2e8` | main workbench band |
| `--surface` | `rgba(255, 251, 243, 0.9)` | rail, composer, elevated controls |
| `--surface-raised` | `#efe8dc` | selected rows, cards, messages |
| `--surface-subtle` | `rgba(248, 241, 229, 0.86)` | status rows and nested panels |
| `--border` | `rgba(111, 133, 172, 0.24)` | hairline borders |
| `--border-strong` | `rgba(94, 108, 255, 0.5)` | active/focus borders |
| `--text` | `#101729` | primary text |
| `--text-muted` | `#536179` | metadata and secondary text |
| `--text-dim` | `#8b98ad` | quiet labels |
| `--accent-blue` | `#2f6df6` | selected state |
| `--accent-green` | `#0fae76` | ready/running signals |
| `--accent-violet` | `#7c3cff` | Kira identity and primary action |
| `--accent-cyan` | `#11c8f5` | ambient glow and gradients |
| `--accent-rose` | `#ff4f9a` | ambient glow and gradients |
| `--accent-amber` | `#c47b1d` | waiting/retry |
| `--danger` | `#df3f58` | errors and destructive states |
| `--radius-sm` | `10px` | inputs and small controls |
| `--radius-md` | `18px` | cards and panels |
| `--font-sans` | `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` | UI text |
| `--font-mono` | `SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace` | code, tool output, IDs |

Use accents as small signals. The Stage 14 default chat surface reads as light/off-white first, with color used for identity, actions, state, and subtle ambient depth. Historical Stage 10/11 dark debug surfaces must not drive the default chat palette.

### Stage 14 Light Chat Mapping

Stage 14 uses the root tokens directly instead of adding a second chat-only
token family.

| Surface | Token | Use |
| --- | --- | --- |
| Canvas | `--canvas`, `--canvas-elevated` | default chat background and centered workbench band |
| Composer and controls | `--surface`, `--border` | quiet bottom composer and elevated controls |
| User prompt | `--surface-raised`, `--border` | right-aligned user bubble |
| Assistant answer | `--text`, `--text-muted` | continuous answer body, timestamp, and action bar |
| Kira identity | `--accent-violet` | agent avatar, focus ring, and primary send action |

## Typography

- App titles: 40-56px, 700 weight, tight line height, no negative letter spacing.
- Panel headings: 13-16px, 700 weight.
- Body text: 14-16px, 1.45-1.6 line height.
- Metadata: 11-13px, muted color.
- Mono snippets: 12px, bounded cards, pre-wrap, internal scroll for long content.

## Layout

### Welcome

- First viewport is a single-agent launch surface.
- Required content: `Kira Agent`, one Kira card whose subtitle is `一个专业的数据agent助手`, and primary `立刻开始`.
- Do not show readiness chips, `Local Web Agent`, `Local agent`, multiple agents, marketing sections, decorative hero art, or hidden thinking.
- Center the launch content vertically and horizontally at desktop and narrow widths.

### Workbench

- Desktop: left task rail plus a chat-first main surface with sticky identity header, centered bounded timeline, and sticky bottom composer.
- The task rail may expose a clear-history affordance that archives active conversations and resets the visible timeline.
- The default workbench must not render the right operator inspector, a prominent `Inspector` entry point, or fixture run buttons.
- Tablet/narrow: rail can collapse away; timeline and composer remain primary.
- Composer stays reachable. Timeline and cards must wrap without horizontal overflow.
- Page sections are structural bands. Use cards only for messages, tools, repeated list items, panels, and modals.

### Stage 11 cis-mira Reference

Stage 11 uses `/Users/bytedance/Desktop/code-agent-set/cis-mira` as a layout and interaction reference only.

Stage 12 expands this into `docs/mira-frontend-study/`. Stage 13 must render conversation turns instead of raw events. Stage 14 rebuilds the default UI as a light Mira-like chat surface. Stage 15 adds browser visual regression.

Adopted patterns:

- `chat-page-ui.tsx` / `chat-page-ui.module.less`: three-section chat ownership where the page is header, scrollable content, and footer; the content column centers children and hides horizontal overflow.
- `chat-footer-ui.tsx`: footer content is constrained by a centered max-width wrapper, matching Kira's bounded composer.
- `mira-page.tsx`: chat orchestration keeps the main conversation first and closes third-column surfaces on session changes; Kira adopts the chat-first default but does not expose the third column by default.
- `message-list-native-scroller.tsx` / `message-list.module.less`: native scroll container, stable bottom scrolling, centered message list, and wrapped overflow behavior.
- `deep-think-shell.tsx`, `deep-think-renderer.tsx`, and `thinking-line-clamp.tsx`: reasoning is a subdued collapsed disclosure by default, with bounded/expandable content inside.
- `prompt-input.tsx` and `use-chat-manager.ts`: successful sends clear prompt state immediately and keep the prompt surface ready for the next input.

Explicitly not adopted by default:

- Slate/contenteditable prompt editor; Kira keeps its simple controlled input.
- Allotment split view and third-column artifact layout; no default right inspector in Stage 11.
- cis-mira design-system dependencies, state libraries, telemetry, or editor packages as a bundle.
- Multi-agent selection and agent marketplace patterns; Kira presents one focused data-agent assistant.

Small stable UX dependencies are allowed later when they clearly improve user experience and stay isolated behind Kira-owned components.

## Timeline Mapping

| Event | Treatment |
| --- | --- |
| `text_delta` | append to the current turn's single assistant answer; visible answer text only |
| `thinking_delta` | collapsed `思考过程` block; never normal answer text |
| `tool_start` | compact `调用工具` row with tool name/scope when present |
| `tool_result` | grouped expandable tool activity with preview, metadata, copy control, bounded scroll |
| `checkpoint` | debug-visible compact marker |
| `interrupt` | waiting row plus focused HITL panel |
| `resume` | user decision marker |
| `retry` | amber attempt row |
| `side_effect_reused` | debug-visible reuse card/row |
| `error` | red failure block with concise message |
| `done` | terminal state and idle composer; no prominent `Completed` card |

Project snippets, memory citations, transcript summaries, replacement stubs, audit records, and traces are metadata surfaces, not assistant answers.

## Components

- `WelcomeScreen`: one centered Kira agent, `一个专业的数据agent助手`, `立刻开始`.
- `TaskRail`: new task, recent conversations/tasks, selected/running/waiting/completed states.
- `AgentWorkbench`: shell only; owns rail, identity row, timeline, composer; no default inspector.
- `RunTimeline`: Stage 13+ turn-based rendering from transcript and live events.
- `ThinkingBlock`: collapsed-by-default `思考过程` disclosure for grouped hidden thinking.
- `ToolCallCard`: `调用工具`, tool name, status, metadata, copy, expand/collapse, bounded preview.
- `HitlPanel`: approval/edit/question controls with visible focus and keyboard submit.
- `PromptComposer`: prompt input, run control, model/profile or fixture/auto indicator, context indicators.
- `InspectorPanel`: skills, project knowledge, memory, diagnostics, audit, trace, replacement inspection only when reached through an explicit non-default debug/developer affordance.

## Safety Rules

- Hidden thinking never appears as normal answer text, visible transcript answer text, or copied final-answer content.
- Provider secrets, raw API keys, bearer tokens, private keys, passwords, and raw replacement blobs must not render in frontend-safe surfaces.
- Redaction and permission decisions from Stage 09 are displayed as metadata, not bypassed by UI formatting.
- Project retrieval text is untrusted data. Show citations and metadata; do not present it as system instruction.

## Responsive And Accessibility

- All controls need accessible names.
- Focus states must be visible on buttons, inputs, selects, textareas, summary toggles, and drawer controls.
- Keyboard users must be able to start, submit, stop, expand thinking/tool cards, and answer HITL.
- Long words, paths, JSON, and snippets must wrap or scroll inside their own card.
- Fixed-format regions such as rail, composer, timeline cards, and tool previews must have stable dimensions.

## Screenshot And Smoke Checklist

- Welcome renders one centered Kira card, `一个专业的数据agent助手`, and `立刻开始`.
- Stage 14 desktop chat shows a light Mira-like conversation, identity row, centered content, and sticky composer without a default inspector.
- Narrow viewport keeps timeline and composer usable without horizontal overflow.
- Running timeline shows `思考过程`, `调用工具`, visible answer, retry/reuse/checkpoint, HITL, error, and subtle done state without scattering the assistant answer.
- Long assistant text and long JSON/tool output stay within containers.
- No-provider-key fixture fallback and diagnostics are visible without raw config values.
- Hidden thinking and secret-like strings do not appear in answer rows or frontend-safe details.
- A single assistant answer never appears as multiple scattered assistant cards.
- Stage 15 browser smoke is run with `pnpm smoke:stage15`; it uses a mock no-key
  API, captures desktop and narrow screenshots for the major conversation
  states, and treats generated screenshots as temporary review evidence rather
  than committed binary baselines.
