## Context

Kira's backend provider layer already supports real OpenAI-compatible streaming through `provider_mode: "auto"` and falls back to fixture when no valid key is available. The current frontend workbench still submits the main composer with `fixture: "welcome"`, which intentionally forces fixture mode and hides the real provider path from the default user flow.

This change is a narrow frontend behavior correction: the primary workbench Run action should behave like a real LLM conversation entry point. Fixture runs remain available, but only through explicit secondary controls.

## Goals / Non-Goals

**Goals:**

- Make the default composer Run action call `POST /api/runs` with `provider_mode: "auto"` and no fixture.
- Add an explicit `Run fixture` action for deterministic local fixture streaming.
- Keep `Run error fixture` and `Run HITL fixture` available for testing/debugging.
- Update tests so they assert request payload intent, not only rendered event output.
- Keep provider metadata redacted and visible enough for users to know whether the run used real provider or fallback fixture.

**Non-Goals:**

- Do not change backend provider selection, config loading, fallback, or streaming behavior.
- Do not remove fixture provider or deterministic tests.
- Do not add multi-turn chat persistence, retrieval, memory, tool-calling LLM loops, or Stage 06+ behavior.
- Do not expose API keys or raw provider config in the frontend.

## Decisions

### Decision: Default composer uses auto provider selection

The composer submit handler SHALL call the existing `startRun()` path with no `fixture` option. `startRun()` already maps absence of fixture to `provider_mode: "auto"`, so this is a small behavior change rather than a new API.

Alternative considered: add a separate "Real LLM" button while leaving Run as fixture. Rejected because the user's expectation is that the primary run button is the actual agent conversation.

### Decision: Keep fixture controls explicit

The workbench SHALL expose a secondary `Run fixture` button for the deterministic welcome fixture. Existing error/HITL fixture buttons remain secondary controls.

Alternative considered: hide fixtures behind settings. Rejected because fixtures are still useful for local debugging and regression testing.

### Decision: Do not change backend fallback semantics

If provider config is missing or invalid, the backend can still select fixture fallback for `provider_mode: "auto"`. The frontend should show provider metadata/fallback reason rather than trying to pre-validate secrets.

Alternative considered: block Run when no real provider is configured. Rejected because Kira's local loop intentionally remains usable without credentials.

## Risks / Trade-offs

- Users without valid keys may still see fixture output -> The inspector continues to show provider mode and fallback reason.
- Existing tests may rely on main Run rendering fixture tool cards -> Move those assertions to the explicit fixture button path.
- Real provider calls can be slower than fixture streams -> Running state already disables composer and shows stop control.

## Migration Plan

1. Change the composer submit handler to call `startRun()` with no fixture.
2. Add `Run fixture` as a secondary inspector action that calls `startRun({ fixture: "welcome" })`.
3. Update prompt/empty-state copy to invite real LLM conversation.
4. Update frontend tests to verify default request payload and explicit fixture request payload.
5. Run frontend tests/typecheck and relevant backend smoke checks if needed.
