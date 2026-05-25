## Why

Kira currently proves the local run loop with deterministic fixtures, but real local agent use requires an OpenAI-compatible LLM provider path. This change adds real provider integration while keeping fixture fallback as the default-safe behavior when no valid API key is configured.

## What Changes

- Add provider configuration loading from `~/.kira-agent/config.yaml` by default, with `KIRA_CONFIG_PATH` override.
- Support provider fields for `api_key`, `base_url`, `model`, `timeout`, `retry`, and default provider selection.
- Add built-in provider presets:
  - `Minimax Global`: `provider: openai`, `baseURL: https://api.minimax.io/v1`
  - `Custom/OpenAI-compatible`: `provider` defaults to `openai`, `baseURL` is user-provided
- Ensure API keys are never committed to the project root and are redacted in logs, API responses, diagnostics, and frontend readiness/provider metadata.
- Add provider selection for default configured provider, per-request provider/model override, explicit fixture runs, and automatic fixture fallback when no valid API key is available.
- Expose redacted run/provider metadata so users can see whether a run used fixture fallback or a real provider without revealing secrets.
- Implement OpenAI-compatible streaming from the local FastAPI server.
- Map remote stream chunks into Kira events:
  - visible assistant content -> `text_delta`
  - `reasoning_content`, thinking fields, or `<think>...</think>` content -> `thinking_delta`
  - normal stream completion -> `done`
  - upstream HTTP/API/parse failures -> `error`
- Ensure hidden thinking is never merged into normal assistant answer text.
- Add a stream parser that tolerates split `<think>` tags across chunks and returns structured provider errors for malformed upstream payloads.
- Add mock-provider tests for config, selection, retries, timeout, redaction, stream mapping, fallback, and upstream failures.
- Add a real smoke test that is skipped unless required env/config is present.

## Capabilities

### New Capabilities

- `llm-provider-config`: Local provider config loading, presets, secret redaction, and readiness metadata.
- `llm-provider-selection`: Provider/model selection across config defaults, request overrides, explicit fixture runs, and missing-key fixture fallback.
- `openai-compatible-streaming`: OpenAI-compatible streaming client and chunk-to-Kira-event mapping for visible text, hidden thinking, completion, and structured errors.

### Modified Capabilities

- None.

## Impact

- Affected backend areas: `server/src/kira_server/providers/`, run request/record models, run event streaming route, app startup/config loading, provider tests, and docs.
- Affected frontend areas: run request types, run/provider readiness metadata display, and hidden-thinking-safe event rendering tests.
- Affected shared contracts: `src/` schemas/examples for redacted provider metadata and provider selection if needed.
- New dependencies may include an async HTTP client such as `httpx`, already available in server dev dependencies but likely needed at runtime.
- Real API keys must live outside the repo by default, under `~/.kira-agent/config.yaml` or a path pointed to by `KIRA_CONFIG_PATH`; project-root secret files remain out of scope.
- Non-goals: Stage 02 tools, LangGraph runtime, checkpointing, memory, project knowledge retrieval, skill workflow runtime, general shell tools, and raw API key exposure to the frontend.
