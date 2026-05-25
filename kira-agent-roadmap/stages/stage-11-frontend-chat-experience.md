# Stage 11: Frontend Chat Experience Hardening

## Goal

Turn the Stage 10 dark workbench from a functional developer cockpit into the default user-facing data-agent chat experience: centered welcome, exact product copy `一个专业的数据agent助手`, `立刻开始` entry action, collapsible `思考过程`, inline tool activity, tight message bubbles, clear-on-submit composer, and no default right-side operator inspector.

## Why This Stage

Stage 10 established the first polished shell, but hands-on review found several product-level issues:

- the welcome page still shows scaffold/runtime copy (`Local Web Agent`, `Local agent`, `FastAPI local`, `Read-only context`, `Auto or fixture`);
- the welcome content is not centered enough for the desired launch experience;
- thinking appears as a permanent row instead of the requested collapsed/expandable `思考过程`;
- tool activity is not strong enough as part of the conversation timeline;
- assistant rows have a large visual gap between the label and answer text;
- submitted prompt text remains in the composer;
- the right inspector exposes internal operator panels by default and makes Kira feel like an admin dashboard.

Stage 11 is intentionally frontend-only. It does not change backend APIs, provider selection, SSE contracts, transcript, skills, memory, graph runtime, project retrieval, audit, trace, or safety boundaries.

## Reference Inputs

- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/components/chat-layout/chat-page-ui.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/components/chat-layout/chat-footer-ui.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/routes/chat-page/mira-page.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/routes/chat-page/components/messages/message-list-native-scroller.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/routes/chat-page/components/messages/message-list.module.less`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/routes/chat-page/components/messages/message-item/deep-think-shell.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/routes/chat-page/components/messages/message-item/deep-think-renderer.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/routes/chat-page/components/messages/message-item/thinking-line-clamp.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/components/prompt-input/prompt-input.tsx`
- `/Users/bytedance/Desktop/code-agent-set/cis-mira/src/hooks/use-chat-manager.ts`

Adopt the layout and interaction ideas, not cis-mira's full dependency stack. Do not import Slate, Allotment, a new design system package, or multi-agent selection.

## Scope

- Update welcome page copy:
  - use `Kira Agent` as brand;
  - use `一个专业的数据agent助手` as the agent/product positioning;
  - remove `Local Web Agent`, `Local agent`, `FastAPI local`, `Read-only context`, `Auto or fixture`;
  - use `立刻开始` as the primary entry action;
  - center content vertically and horizontally.
- Remove the default right-side operator inspector from the workbench:
  - no default `Conversations`, `Skills`, `Memory`, `Project`, `Context`, or `Safety` panels;
  - no default `Run fixture`, `Run error fixture`, or `Run HITL fixture` buttons;
  - no prominent default `Inspector` header button.
- Keep any retained diagnostics behind an explicit non-default developer/debug affordance, route, or environment flag.
- Add collapsed-by-default `思考过程` rendering for `thinking_delta`.
- Add inline `调用工具` activity blocks for `tool_start` / `tool_result`.
- Refactor user and assistant messages into tight chat bubbles with stable spacing.
- Clear and refocus the composer after a successful run creation.
- Update `web/DESIGN.md` so future frontend edits follow the Stage 11 contract.

## Design Contract

### Welcome

The welcome screen should feel like a focused product entry, not a backend status board. It has one centered Kira agent card and one primary action. Runtime readiness details belong in diagnostics/debug surfaces, not in the first viewport.

### Workbench

Default desktop layout:

| Region | Behavior |
| --- | --- |
| Left rail | New task, active/recent conversations, compact status |
| Main header | Kira identity, minimal status/provider metadata |
| Timeline | User prompts, `思考过程`, tool activity, assistant answers, HITL/error/done rows |
| Composer | Sticky bottom input or running/stop state |

No right inspector is visible by default.

### Timeline

| Event | Stage 11 Treatment |
| --- | --- |
| `text_delta` | Tight assistant bubble; visible answer only |
| `thinking_delta` | Collapsed `思考过程` row; opens on click/keyboard |
| `tool_start` | Compact `调用工具` row with tool name/status |
| `tool_result` | Grouped/bounded expandable preview with copy affordance |
| `interrupt` | HITL row plus focused resume panel |
| `resume` | User decision marker |
| `retry` | Compact attempt row |
| `side_effect_reused` | Debug-visible reuse marker/card |
| `error` | Concise red/amber failure row |
| `done` | Completion row and idle composer |

Hidden thinking and tool output never become assistant answer text.

## Implementation Tasks

1. Add Stage 11 notes to `web/DESIGN.md`, including cis-mira reference files and adopted/non-adopted patterns.
2. Update `WelcomeScreen` copy, remove readiness chips, center layout, and change the primary action to `立刻开始`.
3. Update `TaskRail`/brand copy to `一个专业的数据agent助手`.
4. Remove the default inspector aside, fixture buttons, and prominent inspector button from `AgentWorkbench`.
5. Keep debug/diagnostic surfaces only behind a non-default route/flag/toggle if still needed.
6. Add `ThinkingBlock` for grouped `thinking_delta`, default collapsed and labeled `思考过程`.
7. Add `ToolActivityBlock` for grouped tool start/result rendering with bounded expandable previews.
8. Refactor assistant and user rows into bubble components with controlled spacing and no default `<p>` margin gaps.
9. Initialize the composer with an empty string and clear/refocus it immediately after successful run creation.
10. Update CSS for centered bounded timeline, sticky header, sticky composer, and narrow viewport behavior.
11. Update tests for welcome copy/centering, no default inspector, `思考过程` toggle, tool activity grouping, assistant spacing, and composer clear-on-submit.
12. Add a browser-level screenshot smoke check if jsdom tests cannot prove visual layout.

## Validation

- `pnpm typecheck` from `kira-agent/web`.
- `pnpm test` from `kira-agent/web`.
- `pnpm build` from `kira-agent/web`.
- `openspec validate stage-11-frontend-chat-experience --type change --strict`.
- Manual or browser screenshot check for desktop and narrow widths:
  - centered welcome with `一个专业的数据agent助手` and `立刻开始`;
  - no default right inspector;
  - `思考过程` collapsed/expanded states;
  - grouped `调用工具` result preview;
  - assistant label and answer text have no oversized gap;
  - composer clears after submit.

## Exit Criteria

- Kira's default web UI feels like a focused professional data-agent assistant, not an operator dashboard.
- The main conversation demonstrates thinking and tool use inline.
- The default workbench has no right inspector/operator panel noise.
- Follow-up implementation agents can use `web/DESIGN.md` and this stage to reproduce the intended interaction consistently.

## Deferred Work

- Reintroducing a refined diagnostics inspector for power users.
- Full i18n beyond the Stage 11 agreed Chinese product copy.
- Multi-agent welcome selection.
- Browser/mobile packaging beyond local web.
