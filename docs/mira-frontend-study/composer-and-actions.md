# Composer And Actions Study

## cis-mira Pattern

cis-mira treats input as a polished interaction surface:

Relevant reference files:

- `src/components/prompt-input/prompt-input.tsx`
- `src/components/prompt-input/prompt-input.css`
- `src/components/prompt-input/send-stop-button.tsx`
- `src/routes/chat-page/components/messages/message-item/answer-operation-bar.tsx`
- `src/routes/chat-page/components/messages/message-item/user-prompt/manus-user-prompt.tsx`

- submitting clears the editor content;
- focus returns to the editor so the next prompt is immediate;
- running state is visible without hiding the conversation;
- user and assistant message actions appear on hover or in a subdued action bar;
- copy/re-edit/like/dislike are visually secondary to the conversation.

## Kira Target

Kira's composer should stay simple until richer input is needed:

- plain text input by default;
- clear on successful submit;
- keep focus after submit;
- keyboard submit and explicit run button;
- stop button while running;
- HITL resume panel replaces or nests near the composer only when needed;
- no stale prompt text after a run starts.

## Optional Future Dependencies

Only add richer input dependencies when the product needs them:

| Need | Possible Dependency Direction |
| --- | --- |
| markdown rendering in answers | small markdown renderer |
| tooltips/action menus | Radix-style primitives or a similar lightweight package |
| rich attachments/mentions/slash commands | consider richer editor only after clear requirements |
| long transcript performance | virtual list library if measured performance needs it |

Do not import the cis-mira Slate editor stack, upload controls, optimizer
controls, agent tags, or data-source dropdowns for Stage 14. Those features need
separate Kira product requirements before they can enter the dependency budget.

## Action Bar

Stage 14 should add a minimal assistant action bar:

- copy answer;
- retry/regenerate if backend support exists, otherwise defer;
- subtle timestamp;
- optional inspect-process action that opens the reasoning/tools section rather
  than an operator dashboard.
