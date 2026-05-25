# Layout And Shell Study

## cis-mira Pattern

cis-mira uses a stable chat page shell:

- a top header area;
- a central scrollable content area;
- a footer/composer area that remains available while the conversation scrolls.

Relevant reference files:

- `src/components/chat-layout/chat-page-ui.tsx`
- `src/components/chat-layout/chat-page-ui.module.less`
- `src/components/chat-layout/chat-footer-ui.tsx`
- `src/routes/chat-page/mira-page.tsx`
- `src/routes/chat-page/components/messages/manus-message-list.tsx`
- `src/routes/chat-page/components/messages/message-list-native-scroller.tsx`

`chat-page-ui.tsx` and `chat-page-ui.module.less` keep the shell simple:
`display: flex`, `flex-direction: column`, a full-height container, and a
scrollable `.content` region. The message list then uses a bounded max-width
layout so wide desktop screens do not stretch answer text across the viewport.

The message scroller is treated as a first-class component. It owns scroll-to-
bottom behavior, initial scroll positioning, and long transcript handling rather
than letting every message block improvise scroll behavior.

## Kira Problem To Fix

The current Kira workbench still feels like an event cockpit:

- the header shows operational metadata that competes with the answer;
- the timeline renders raw event blocks too directly;
- the completed state can appear as a loud card;
- debug/inspector surfaces have historically been too close to the default
  conversation surface.

## Kira Target

Kira's default shell should be:

| Region | Target |
| --- | --- |
| Welcome | centered single-agent launch with `一个专业的数据agent助手` and `立刻开始` |
| Chat header | minimal conversation/model identity, no event-count dashboard feel |
| Messages | scrollable, bounded, turn-based conversation content |
| Composer | sticky bottom input, clear-on-submit, stop/resume states |
| Diagnostics | non-default debug route/drawer/panel, never the first surface |

## Implementation Guidance

- Use Kira-owned CSS/layout modules first. Introduce a dependency only when the
  experience benefit is clear and the dependency is not tied to cis-mira business
  state.
- Do not copy cis-mira split-pane behavior or `Allotment` by default. Kira's
  diagnostics must stay non-default unless a later proposal proves a user need.
- Keep the default view light and conversation-first for Stage 14.
- Treat the left rail as optional/secondary for the Mira-like direction; the
  conversation must remain usable without relying on a dashboard rail.
- Prevent horizontal overflow at narrow widths by constraining message max width,
  composer controls, code blocks, and tool previews.
