## Why

The backend can already select and stream from a real OpenAI-compatible provider, but the primary frontend Run action still forces the deterministic `welcome` fixture. This makes the app look like a fixture demo even when a valid real LLM is configured.

## What Changes

- Change the workbench default prompt/composer path so `Run` creates a run with `provider_mode: "auto"` and does not pass `fixture`.
- Keep deterministic fixture access explicit through a separate `Run fixture` button.
- Keep the existing error fixture and HITL fixture controls available as test/demo actions.
- Update visible workbench copy so the primary surface reads like a real LLM conversation entry point, not a fixture-only demo.
- Preserve fixture fallback behavior: if no valid API key exists, backend auto selection can still fall back to fixture and expose the redacted fallback reason.
- Add frontend tests proving the default Run request does not include fixture and the explicit fixture button still does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `local-web-workbench`: The default workbench Run action starts an auto provider-selected LLM run instead of a fixture-backed run, while fixture demos remain explicit secondary controls.

## Impact

- Frontend: `web/src/components/AgentWorkbench.tsx`, workbench labels, and existing workbench tests.
- API usage: the default frontend run request changes from `{ fixture: "welcome", provider_mode: "fixture" }` to `{ provider_mode: "auto" }` without backend API changes.
- Backend: no provider selection or streaming changes required.
- Shared contracts: no schema changes required.

## Scope

- Only the default workbench run interaction and related tests/docs.
- Keep all existing provider selection, fixture fallback, HITL fixture, SSE rendering, and redaction behavior.

## Non-goals

- Do not change backend provider selection rules.
- Do not remove fixture provider or fixture tests.
- Do not add chat history, memory, retrieval, tool-calling model loops, or Stage 06+ features.
- Do not expose raw API keys or provider config in the frontend.

## Acceptance Criteria

- Clicking the main `Run` button sends a run creation request with `provider_mode: "auto"` and no `fixture` field/value.
- Clicking `Run fixture` sends an explicit deterministic fixture request.
- The workbench default prompt and empty state invite a real LLM conversation.
- Provider metadata in the inspector shows the real provider/model when configured, or fixture fallback reason when auto selection falls back.
- Existing error fixture and HITL fixture controls still work.

## Risks

- Users without a valid API key may still see fixture output due to intentional fallback; the provider metadata must make that clear.
- Tests that assumed the main Run button was fixture-backed need to move to the explicit fixture button.
