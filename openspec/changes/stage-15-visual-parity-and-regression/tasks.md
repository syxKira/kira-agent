## 1. Fixture States

- [x] 1.1 Add deterministic fixture data for welcome, normal answer, streaming, reasoning, tool call, HITL, error, and long transcript states.
- [x] 1.2 Ensure fixtures do not require a real provider key.

## 2. Browser Smoke

- [x] 2.1 Add or extend a local browser smoke command.
- [x] 2.2 Capture desktop and narrow viewport states.
- [x] 2.3 Add DOM assertions for prominent `Completed`, scattered assistant answers, default inspector visibility, thinking default-open state, and composer residue.

## 3. Documentation And Verification

- [x] 3.1 Document the smoke command and baseline update policy.
- [x] 3.2 Run `pnpm test`, `pnpm build`, the browser smoke command, and `openspec validate stage-15-visual-parity-and-regression --type change --strict`.
