# Kira Target UI Spec

## Product Direction

Kira's default web UI should feel like a professional data-agent assistant. The
first experience is a centered welcome screen; the main experience is a clean
Mira-like chat, not a developer event dashboard.

## Welcome

- Brand: `Kira Agent`.
- Positioning copy: `一个专业的数据agent助手`.
- Primary action: `立刻开始`.
- One agent only.
- No `FastAPI local`, `Read-only context`, `Auto or fixture`, event-count, or
  fixture/debug copy in the first viewport.

## Chat

Default Stage 14 visual direction:

- light/off-white canvas;
- right-aligned user bubble in a soft neutral surface;
- assistant model identity row on the left, such as `Kira` or selected model
  display name;
- answer text rendered as continuous readable content, not as many bordered
  assistant cards;
- collapsed `思考过程` near the assistant process;
- tool activity nested into the process/answer flow;
- subtle action icons under the assistant answer;
- composer fixed to the bottom and visually quiet.

## Must Not Regress

- One user prompt must not create multiple scattered assistant answer cards.
- `Completed` must not appear as a loud main card.
- Thinking must not default to visible expanded content.
- Tool output must not become answer text.
- The prompt input must not retain submitted text after successful submit.
- Inspector/debug panels must not appear in the default chat surface.

## Complaint To Stage Mapping

| Failure Pattern | Owning Stage |
| --- | --- |
| one prompt creates scattered assistant answer blocks | Stage 13 aggregation |
| `Completed` appears as a loud primary card | Stage 13 aggregation, Stage 14 rendering |
| thinking or tool rows look like a dashboard instead of process disclosure | Stage 13 aggregation, Stage 14 rendering |
| default UI exposes fixture controls, event counts, or inspector panels | Stage 14 default shell |
| submitted prompt text remains in the composer | Stage 14 composer behavior |
| narrow or desktop screenshots show overlap, overflow, or dashboard drift | Stage 15 visual regression |
| screenshots do not prove welcome/chat/HITL/tool/error states | Stage 15 visual evidence |

## Screenshot Acceptance

Stage 15 screenshots should cover:

- welcome desktop;
- welcome narrow;
- normal assistant answer;
- streaming/status phase;
- collapsed and expanded `思考过程`;
- tool activity with long JSON/text;
- HITL interrupt/resume;
- error state;
- long transcript.

Screenshots fail if the UI resembles an event log more than a conversation.
