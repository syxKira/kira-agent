## 1. Config And Redaction

- [x] 1.1 Add provider config models for `api_key`, `base_url`/`baseURL`, `model`, `timeout`, `retry`, `provider`, `preset`, and default provider selection.
- [x] 1.2 Implement config loading from `~/.kira-agent/config.yaml` with `KIRA_CONFIG_PATH` override.
- [x] 1.3 Add `Minimax Global` preset with `provider: openai` and `baseURL: https://api.minimax.io/v1`.
- [x] 1.4 Add custom OpenAI-compatible config support where provider defaults to `openai` and base URL is user-provided.
- [x] 1.5 Implement centralized API key redaction helpers for config, logs, errors, API responses, diagnostics, and frontend metadata.
- [x] 1.6 Add docs and examples showing config lives outside project root and real API keys must not be committed.

## 2. Run Contracts And Provider Selection

- [x] 2.1 Extend backend run request models with provider override, model override, and fixture/real provider mode selection.
- [x] 2.2 Extend run records and responses with redacted provider metadata.
- [x] 2.3 Implement provider selection using config defaults when valid credentials exist.
- [x] 2.4 Implement per-request provider override without mutating saved config.
- [x] 2.5 Implement per-request model override with redacted selected-model metadata.
- [x] 2.6 Preserve explicit fixture runs and deterministic fixture scripts.
- [x] 2.7 Implement missing/invalid API key fallback to fixture with fallback reason metadata.
- [x] 2.8 Ensure provider selection metadata never includes raw API keys.

## 3. OpenAI-Compatible Streaming Provider

- [x] 3.1 Add runtime HTTP dependency if needed and implement async OpenAI-compatible streaming client.
- [x] 3.2 Build chat completion streaming requests from selected provider config and run prompt.
- [x] 3.3 Apply configured timeout to request and stream reading.
- [x] 3.4 Apply configured retry policy before stream output begins.
- [x] 3.5 Return structured provider errors for non-2xx responses.
- [x] 3.6 Return structured provider errors for timeout and retry exhaustion.
- [x] 3.7 Ensure fixture provider remains the safe fallback and default test path.

## 4. Stream Mapping

- [x] 4.1 Implement chunk parser for OpenAI-compatible SSE `data:` lines and `[DONE]`.
- [x] 4.2 Map visible assistant `content` deltas to `text_delta`.
- [x] 4.3 Map `reasoning_content` or provider thinking fields to `thinking_delta`.
- [x] 4.4 Parse `<think>...</think>` sections into `thinking_delta` while preserving visible content as `text_delta`.
- [x] 4.5 Make `<think>` parser tolerate opening and closing tags split across chunks.
- [x] 4.6 Emit exactly one `done` event on normal upstream completion.
- [x] 4.7 Emit structured `error` events for malformed JSON or unsupported stream payloads.
- [x] 4.8 Ensure hidden thinking is never merged into normal assistant answer text.

## 5. API And Frontend Readiness

- [x] 5.1 Wire `/api/runs/{thread_id}/events` to selected provider instead of unconditional fixture provider.
- [x] 5.2 Add optional redacted provider readiness/status metadata endpoint or include equivalent metadata in existing run/readiness responses.
- [x] 5.3 Update TypeScript run request/response types for provider/model overrides and redacted provider metadata.
- [x] 5.4 Update frontend readiness and running-state labels so fixture fallback and real provider selection are visible without exposing secrets.
- [x] 5.5 Keep frontend answer rendering unchanged for hidden thinking safety.

## 6. Mock And Unit Tests

- [x] 6.1 Add config loading tests for default path, `KIRA_CONFIG_PATH`, Minimax preset, custom provider, invalid config, and redacted errors.
- [x] 6.2 Add redaction tests proving raw API keys are absent from public metadata, errors, logs/diagnostics helpers, and frontend-facing payloads.
- [x] 6.3 Add provider selection tests for config default, per-request provider override, per-request model override, explicit fixture mode, and missing-key fallback.
- [x] 6.4 Add retry and timeout tests with mocked upstream responses.
- [x] 6.5 Add stream mapping tests for visible content, `reasoning_content`, thinking fields, `<think>` content, and split `<think>` tags.
- [x] 6.6 Add upstream failure tests for non-2xx, timeout, malformed stream payloads, and retry exhaustion.
- [x] 6.7 Add fixture fallback tests proving no real API key is required by default.
- [x] 6.8 Add frontend tests proving redacted provider metadata renders and raw API keys do not appear.

## 7. Smoke And Validation

- [x] 7.1 Add a real provider smoke test that is skipped unless explicit env/config opt-in is present.
- [x] 7.2 Ensure default backend and frontend tests do not require real API keys.
- [x] 7.3 Run backend tests, frontend tests/typecheck where touched, and OpenSpec validation.
- [x] 7.4 Record verification commands and results in the implementation summary.
