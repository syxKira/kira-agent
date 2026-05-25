## 1. Workbench Behavior

- [x] 1.1 Change the default prompt text to invite a real LLM conversation instead of the welcome fixture.
- [x] 1.2 Change the main composer `Run` submit path to call `startRun()` without a fixture.
- [x] 1.3 Ensure the default run request uses `provider_mode: "auto"` and does not include a fixture value.
- [x] 1.4 Add an explicit `Run fixture` secondary control that calls the deterministic welcome fixture.
- [x] 1.5 Keep `Run error fixture` and `Run HITL fixture` secondary controls working.
- [x] 1.6 Update empty-state or visible workbench copy that still implies the primary run is fixture-backed.

## 2. Tests

- [x] 2.1 Update frontend workbench tests so the main `Run` action asserts no fixture is sent and `provider_mode` is `auto`.
- [x] 2.2 Add or update a test for the explicit `Run fixture` control rendering fixture timeline groups.
- [x] 2.3 Keep existing tests for error fixture, HITL fixture, provider redaction, hidden thinking filtering, and responsive layout.
- [x] 2.4 Run `pnpm test`.
- [x] 2.5 Run `pnpm typecheck`.

## 3. Documentation And Validation

- [x] 3.1 Update README/web-facing docs to say the default workbench Run uses provider auto selection.
- [x] 3.2 Document that fixture runs remain available through explicit fixture controls.
- [x] 3.3 Run `openspec validate "default-workbench-real-llm-run" --strict`.
- [x] 3.4 Run `openspec status --change "default-workbench-real-llm-run"` and confirm all artifacts are complete.
- [x] 3.5 Record verification commands and results in the implementation summary.
