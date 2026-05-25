## Context

Kira has a local FastAPI run loop and fixture-backed SSE stream. The current provider boundary exists, but `OpenAICompatibleProvider` is only a stub and `/api/runs/{thread_id}/events` always streams fixture events. The frontend also assumes fixture mode in its labels and request shape.

This change adds the provider layer needed to call a real OpenAI-compatible LLM API from the local server. It keeps fixture as the deterministic fallback for tests and for machines without a configured API key. The implementation must preserve the Stage 01 event contract: provider output is normalized to `text_delta`, `thinking_delta`, `done`, and `error`, and hidden thinking is not rendered as normal assistant text.

## Goals / Non-Goals

**Goals:**

- Load provider config from `~/.kira-agent/config.yaml` by default and from `KIRA_CONFIG_PATH` when set.
- Support `api_key`, `base_url`, `model`, `timeout`, and `retry` config fields.
- Provide redaction utilities so API keys never appear in logs, API responses, diagnostics, tests, or frontend readiness state.
- Include a `Minimax Global` OpenAI-compatible preset and a custom OpenAI-compatible provider mode.
- Select provider from config defaults, per-request provider/model overrides, explicit fixture mode, or fixture fallback when no valid key exists.
- Surface redacted run/provider metadata for user visibility.
- Implement OpenAI-compatible streaming using the local FastAPI server as the caller.
- Map remote stream chunks into Kira events, including visible text, hidden thinking, completion, and structured provider errors.
- Add mock-provider tests and skipped real smoke coverage that never requires a real key by default.

**Non-Goals:**

- No Stage 02 tool implementation or changes.
- No LangGraph runtime, `ToolNode`, checkpointing, memory, project knowledge retrieval, or skill workflow runtime.
- No general shell tool.
- No raw API key exposure to frontend or API callers.
- No hosted deployment or production auth.

## Decisions

### Config lives outside the project root by default

The provider config loader reads `~/.kira-agent/config.yaml` unless `KIRA_CONFIG_PATH` points elsewhere. Documentation and tests should treat project-root secret files as invalid practice, and `.env`/local config examples must never include real keys.

Alternative considered: load `.env` or project-local YAML by default. That is convenient but increases the chance of committing secrets in the repo.

### Normalize config field names but preserve preset names

Config parsing should accept `baseURL` for preset compatibility and normalize it internally to `base_url`. The Minimax preset must be available as:

```yaml
preset: Minimax Global
provider: openai
baseURL: https://api.minimax.io/v1
```

Custom/OpenAI-compatible config defaults `provider` to `openai` and requires user-provided `baseURL` or `base_url`.

### Provider selection returns redacted metadata

Selection should produce an internal selected-provider object with secrets and a public metadata object without secrets. Run responses and event metadata can include provider name, preset, model, base URL host or redacted URL, source (`config`, `request_override`, `fixture`, `fallback`), and fallback reason, but never `api_key`.

Alternative considered: expose full selected config to simplify debugging. That is not acceptable because the frontend receives run metadata.

### Missing API key degrades to fixture

If a request asks for a real provider but no valid key is available, the backend should create the run and select the fixture provider with `fallback_reason: missing_api_key`. This preserves the local web loop and keeps tests deterministic.

Alternative considered: fail run creation when provider credentials are missing. That would make the local app feel broken on first launch.

### Use OpenAI-compatible chat completions streaming

The real provider should call an OpenAI-compatible chat completion streaming endpoint under the configured `base_url`, model, timeout, and retry settings. The implementation should use an async HTTP client with explicit timeout and retry behavior. Tests should use mocked HTTP streams.

Alternative considered: add provider SDKs. That would add provider-specific behavior and dependencies too early.

### Parse thinking separately from visible content

The stream mapper should emit `text_delta` for visible assistant content and `thinking_delta` for `reasoning_content`, provider thinking fields, and content enclosed in `<think>...</think>`. The parser must tolerate split `<think>` and `</think>` tags across chunks.

Alternative considered: pass all assistant content through as `text_delta`. That would violate Kira's hidden-thinking separation.

## Risks / Trade-offs

- Config formats vary by provider -> Accept `baseURL` and `base_url`, keep provider type `openai`, and add clear validation errors.
- Redaction gaps can leak secrets -> Centralize redaction and test API responses, metadata, diagnostics, and error paths.
- Streaming parsers are easy to get wrong -> Unit-test split `<think>` tags, malformed server-sent events, non-JSON chunks, and mixed visible/thinking deltas.
- Retry logic can duplicate output -> Apply retries only before a stream has yielded provider content, or return structured error once streaming has started.
- Upstream failures could break local UI -> Convert non-2xx, timeout, malformed stream, and retry exhaustion into `error` events.
- Real smoke tests can be flaky or expensive -> Skip unless explicit env/config opt-in is present.

## Migration Plan

1. Add config models, loader, presets, redaction helpers, and provider readiness metadata.
2. Extend run request/record/response types to include provider/model override and redacted provider metadata.
3. Implement provider selection that supports fixture, config default, per-request overrides, and missing-key fixture fallback.
4. Implement an OpenAI-compatible streaming provider and chunk parser.
5. Wire `/api/runs/{thread_id}/events` to selected provider instead of unconditional fixture.
6. Update frontend request types and readiness/run metadata labels without exposing secrets.
7. Add mock-provider tests, fallback tests, upstream failure tests, parser tests, and skipped real smoke test.

Rollback is removing the real provider modules and reverting run selection to fixture-only behavior while leaving fixture provider and Stage 02 tools intact.

## Open Questions

- Whether to expose a small `GET /api/provider/status` endpoint or only include redacted provider metadata in run responses/readiness. The implementation can choose the smaller surface that satisfies UI readiness needs.
- Exact real-smoke opt-in names should be decided during implementation, for example `KIRA_REAL_LLM_SMOKE=1` plus a config path or environment-backed temporary config.
