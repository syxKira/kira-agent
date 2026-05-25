# Appendix: Tech Choices

## Runtime And Framework

| Area | Choice | Reason |
| --- | --- | --- |
| Backend language | Python | Matches requested runtime and LangGraph/LangChain ecosystem |
| Backend framework | FastAPI | Local API, SSE, typed request/response models |
| Frontend language | TypeScript | Strong contracts for event/state UI |
| Frontend framework | Vite React | Fast local dev and simple app shell |
| Provider | OpenAI-compatible + fixture | Real model path plus deterministic tests |
| Storage | SQLite | Local checkpoint, session projection, memory, audit, traces |

## LangChain Usage

Kira uses only `langchain-core` tool primitives:

- `@tool` decorator;
- `BaseTool`;
- schema inference / JSON Schema;
- argument validation and invocation compatibility with LangGraph `ToolNode`.

Kira does not use LangChain agents, chains, memory, prompt templates, or provider abstraction as a product dependency.

## Provider Configuration

Kira's real model path is OpenAI-compatible and remains separate from LangChain. The focused real LLM provider change establishes the provider contract that later stages consume:

| Area | Decision |
| --- | --- |
| User config path | `~/.kira-agent/config.yaml`, overridable by `KIRA_CONFIG_PATH` |
| Profile shape | `preset`, `provider`, `baseURL`, `apiKey`, `model`, timeout, retry |
| Preset | `Minimax Global` maps to `provider: openai` and `baseURL: https://api.minimax.io/v1` |
| Custom provider | OpenAI-compatible, `provider` defaults to `openai`, user supplies `baseURL` |
| Selection order | run request override -> skill model hint -> configured default -> fixture fallback |
| No-key behavior | degrade to fixture provider when local policy permits |
| Redaction | API keys are never exposed to frontend, logs, traces, checkpoints, memory, or skill manifests |
| Stream mapping | remote visible content -> `text_delta`; reasoning/thinking/`<think>` -> `thinking_delta`; normal finish -> `done`; upstream failure -> `error` |

Later stages should not reimplement provider chunk parsing. They should consume normalized KiraEvents and redacted provider metadata.

## LangGraph Usage

Kira uses only:

- `StateGraph`;
- `ToolNode`;
- conditional edges;
- SQLite checkpointer;
- `interrupt`;
- `astream_events`.

Core does not use `create_agent` or prebuilt agent loops. Workflow semantics come from skills.

Kira's reliability layer around LangGraph uses:

- SQLite checkpointer as graph state authority;
- `thread_id` as the run/resume/lock key;
- per-run event sequence for SSE replay;
- Kira-owned run locks and side-effect ledger tables;
- explicit retry, timeout, cancellation, and repair policy.

## Local File Retrieval

Stage 02 exposes primitive read-only tools:

| Tool | Default implementation |
| --- | --- |
| File listing | Prefer `rg --files`; Python fallback |
| Text search | Prefer `rg`; Python fallback |
| File read | Python text read with binary/size/path checks |
| Ignore policy | built-in ignores plus `.gitignore` where practical |

Stage 06 upgrades those tools into a project knowledge retrieval system:

| Layer | Default implementation |
| --- | --- |
| Inventory | SQLite file metadata with mtime/size/hash and ignore reason |
| Chunking | line-aware text chunks with stable chunk IDs and source maps |
| Search | live `rg` plus SQLite FTS5 where available |
| Citations | path, line range, chunk hash, indexed-at time, stale flag |
| Context packing | ContextItem budget with included/truncated/omitted trace |

The file tools and retrieval system are read-only with respect to project files. Index/cache writes are Kira-owned local data.

## Python Execution

`run_python_script` runs Python subprocesses with:

- project-root cwd constraint;
- env allowlist;
- timeout;
- stdout/stderr caps;
- no shell expansion;
- structured result;
- audit record;
- optional HITL approval.

## Skill And Memory References

- Kai Stage 10 is the baseline for discovery, catalog, explicit activation, auto routing, progressive loading, and the manual memory precursor.
- Kai Stage 13 is the baseline for typed/scoped memory, extraction candidates, citations, secret guard, and lifecycle.
- Claude-style skill frontmatter informs richer fields such as `allowed-tools`, `model`, `effort`, `context`, invocation gates, and hooks.
- Codex-style skill anatomy informs the required `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and UI metadata.

## References

- LangChain tools: <https://docs.langchain.com/oss/python/langchain/tools>
- LangChain Core `tool`: <https://reference.langchain.com/python/langchain-core/tools/convert/tool>
- LangGraph `ToolNode`: <https://reference.langchain.com/python/langgraph.prebuilt/tool_node/ToolNode>
- LangGraph `StateGraph.compile`: <https://reference.langchain.com/python/langgraph/graph/state/StateGraph/compile>
- LangGraph interrupts: <https://docs.langchain.com/oss/python/langgraph/interrupts>
- LangGraph durable execution: <https://docs.langchain.com/oss/python/langgraph/durable-execution>
- LangGraph persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
- OWASP prompt injection: <https://genai.owasp.org/llmrisk/llm01-prompt-injection/>
