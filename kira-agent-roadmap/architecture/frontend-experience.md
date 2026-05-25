# Frontend Experience

Kira's frontend should feel like a focused professional data-agent assistant, not a generic admin dashboard. The first viewport is a centered welcome screen. After the user clicks `立刻开始`, the app enters a conversation-first workspace: user requests on the right, assistant identity and answer content on the left, `思考过程` as a collapsed disclosure, tool calls as structured inline process cards, and a bottom control area for input or Stop.

Stage 10 and Stage 11 produced the first dark workbench and hardening pass. Stage 12-15 supersede that as the main frontend direction: study cis-mira, aggregate events into turns, rebuild the default UI as a light Mira-like chat surface, and lock the result with visual regression.

## View Structure

| View | Purpose | Stage |
| --- | --- | --- |
| Welcome | Start local agent session and guide first action; Stage 10 creates one Kira launch card, Stage 11 centers it and removes runtime scaffold copy, Stage 14 aligns it to the Mira-like chat product | Stage 01, Stage 10-11, Stage 14 |
| Workbench | Main run surface with prompt composer, turn-based conversation, stop/resume controls; Stage 13 removes raw-event rendering and Stage 14 rebuilds the default light chat UI | Stage 01, Stage 10-14 |
| HITL Panel | Approval/edit/question UI surfaced from `interrupt` | Stage 05 |
| Conversation Transcript | Conversation list, visible prior turns, active head, fork/rollback, compaction/replacement trace, follow-up continuity | Stage 08 |
| Inspectors | Skills, tools, project knowledge, memory, transcript, state, context debug, audit/trace details; Stage 11 removes these from the default chat surface | Stage 06-09, Stage 11 |
| Design Contract | `web/DESIGN.md` plus `docs/mira-frontend-study/` with tokens, component rules, turn mapping, responsive checks, and cis-mira study notes | Stage 10-15 |

## Welcome Screen

The welcome screen is not a marketing page. It is a calm launch surface for local work:

- product name `Kira Agent`;
- short description: `一个专业的数据agent助手`;
- `立刻开始` button as the primary action;
- one Kira agent card only; no multi-agent selection in v0;
- no first-viewport runtime scaffold chips such as `FastAPI local`, `Read-only context`, or `Auto or fixture`;
- optional recent conversations list once Stage 08 exists;
- secondary links for Tools, Skills, and Settings can be disabled until their stages exist.

The Start action transitions to the Workbench. It may create an empty local session before the first prompt, but it should not require a model call.

## Workbench Layout

The Workbench has three zones:

| Zone | Contents |
| --- | --- |
| Main timeline | User prompts, assistant status, streamed text, tool cards, HITL rows, completion/error states |
| Left rail | Conversation/task list, new task action, status/time metadata; introduced in Stage 10 polish after Stage 08 continuity |
| Right inspector | Not visible by default after Stage 11; diagnostics/debug surfaces can return only through explicit non-default developer affordances |
| Bottom bar | Prompt composer when idle; Stop button and progress summary when running |

The Stage 10/11 UI used a dark focused shell. Stage 14 changes the default product surface to a light Mira-like chat, while diagnostics/debug surfaces may keep the dark technical styling if that remains useful. Avoid decorative hero art, gradient blobs, and card-heavy marketing composition. Tool cards can be framed; page sections should remain unframed.

## Timeline Blocks

| Event | Block |
| --- | --- |
| User prompt | Right-aligned soft bubble with timestamp |
| Thinking/status | Collapsed-by-default `思考过程` row with a caret |
| Tool start | Compact `调用工具` row plus tool name/status |
| Tool result | Structured card with language/type label, JSON/result preview, copy button, expand/collapse |
| Retry | Compact status row with attempt count and reason |
| Side-effect reuse | Debug-visible marker showing a completed action was reused rather than re-executed |
| Assistant text | One continuous assistant response region with identity row, no repeated assistant cards |
| Interrupt | Waiting row plus HITL panel asking for approval/edit/question |
| Resume | User decision marker in timeline |
| Error | Red/amber row with concise message and retry/resume action when possible |
| Done | Terminal state and idle composer; no prominent `Completed` card |

Hidden thinking is never rendered as normal answer text. It is available as a collapsed `思考过程` row, but it must not be persisted into visible transcript history as answer text.

## Component Inventory

| Component | Responsibility |
| --- | --- |
| `WelcomeScreen` | Start local session, readiness checks, recent runs placeholder |
| `AgentWorkbench` | Own layout shell and active run state |
| `TaskRail` | New task action, conversation/task list, running/interrupted/completed state |
| `TranscriptView` | Render persisted visible user/assistant turns and current streaming response |
| `PromptComposer` | Text input, submit, disabled/running states |
| `RunTimeline` | Render turn view models from transcript and live KiraEvents |
| `AgentStatusRow` | Thinking, waiting, completed, and error states |
| `ToolCallCard` | Tool name, schema/result preview, copy, expand/collapse |
| `HitlPanel` | Approval/edit/question response and resume submission |
| `ProjectKnowledgePanel` | Index status, search results, citations, stale files, omitted snippets |
| `InspectorPanel` | Skills, tools, project knowledge, memory, state, context, trace tabs; non-default after Stage 11 |
| `StopRunButton` | Abort active stream/run when backend supports it |
| `DesignTokens` | CSS variables or theme module generated from `web/DESIGN.md` |

## Responsive Behavior

- Desktop: left task rail, centered timeline, no default right inspector, fixed bottom composer.
- Narrow screens: inspector moves behind tabs or a drawer; timeline remains the primary surface.
- Mobile/narrow: task rail collapses to a drawer or top sheet; composer remains reachable.
- Text in bubbles/cards must wrap cleanly and never overlap controls.
- Tool result cards should have stable max height with internal scroll/expand.

## Acceptance Checks

- Welcome screen renders without backend events and Start enters Workbench.
- Fixture run renders user bubble, collapsed `思考过程`, `调用工具` strip/card, JSON tool card, one continuous assistant answer, and subtle done state.
- Running state swaps composer for Stop control.
- HITL interrupt opens an inline marker and focused panel, then resume adds a user decision marker.
- Retry, cancellation, and side-effect reuse events are visible in the timeline without exposing raw internals by default.
- Project knowledge inspector shows cited snippets and stale markers from a fixture retrieval.
- Hidden thinking does not appear as normal text.
- Desktop and narrow viewport screenshots show no overlapping text or controls.
- Stage 15 visual smoke tests cover the Mira-like welcome and chat surfaces, task/conversation access, composer, tool cards, HITL, errors, long text, no default inspector, no loud `Completed` card, and clear-on-submit behavior.
