# 00 Design Principles

Kira is a general local agent, not a code agent with a renamed UI. The roadmap keeps the durable agent parts from Kai and removes code mutation, repo patching, and terminal-first interaction.

## Core Principles

| Principle | Meaning |
| --- | --- |
| Local web first | The primary experience is FastAPI + Vite React running locally, not CLI/TUI/Ink |
| Python backend first | Agent runtime, tools, storage, and graph orchestration are implemented in Python |
| TypeScript frontend | The frontend is TypeScript and treats backend events as the source of run truth |
| Skill-driven workflows | Core provides graph runtime; skills provide concrete business workflows |
| Tool protocol first | Tools are `langchain-core` `@tool` / `BaseTool` objects with JSON Schema and validation |
| Read-only project context | Project files can be discovered, searched, and read, but not modified |
| Controlled local execution | Python scripts and shell commands run with cwd/env/timeout/output/audit boundaries |
| Reliable graph runtime | Graph state uses SQLite checkpointing plus run locks, idempotency, retry policy, and side-effect ledger |
| HITL as protocol | Human approval/edit/question flows use `interrupt` and API/SSE events, not UI-private state |
| ContextItem budget | Skill, memory, project files, history, and tool results enter model input through one budgeted path |
| Fixture first for tests | Deterministic provider and graph fixtures are required for CI and local regression |
| Provider secrets stay local | Real provider config is loaded from user-local config/env and only redacted metadata enters runtime state |
| No hidden LangChain expansion | Do not adopt LangChain agents/chains/memory/prompt templates without a new roadmap decision |

## Reused From Kai

| Kai capability | Kira adaptation |
| --- | --- |
| Provider abstraction | OpenAI-compatible adapter plus fixture adapter |
| Stream/thinking separation | Provider events distinguish visible text from hidden thinking |
| Tool protocol | Implemented through LangChain Core tools instead of Kai TS ToolDef |
| HITL manager idea | Implemented through LangGraph interrupt and FastAPI resume |
| Session/replay | Implemented through SQLite checkpointer, session projection, run events, and side-effect ledger |
| Context Kernel | ContextItem remains the unit for budgeted model input |
| Skills | Skills become the workflow/tool/context extension unit |
| Memory system | Start conservative, then use typed/scoped/cited memory with lifecycle and ContextItem injection |
| Permission/audit | Applied to Python/shell execution, project file reads, workflow actions, and skill capabilities |

## Removed From Kai

| Removed capability | Reason |
| --- | --- |
| CLI/TUI/Ink primary shell | Kira is a web app agent |
| Coding/build profile | Kira is not specialized for code tasks |
| write/edit/apply_patch | Project files are read-only context in Kira v0 |
| patch safety | No patch tool exists |
| LSP/diagnostics/git diff | Code-agent-specific context and validation |
| unbounded shell | Too broad; Kira only exposes controlled shell execution with project-root, timeout, output, redaction, and audit boundaries |
| hardcoded business graph | Workflows must come from skills |

## Project Knowledge Retrieval Principles

Project-local retrieval is a general agent capability. It lets Kira answer from local project documents, data files, configuration, notes, and source text when relevant, but it is not a code editing system. The first file tools are only the I/O boundary; the roadmap matures them into a retrieval system with inventory, chunks, ranking, citations, freshness checks, and ContextItem packing.

Project-bound default-agent runs expose project search/read tools and let the model retrieve local documents on demand when the task needs business facts, citations, or project-specific background. Explicit project context queries can still pre-inject bounded snippets, and prompt-derived preloading is available only through opt-in automation.

| Rule | Meaning |
| --- | --- |
| Root anchored | Every file path resolves inside the selected project root |
| Read-only | Tools never write, move, delete, patch, format, or stage files |
| rg first | Listing/search prefer `rg`; Python fallback is only for environments without `rg` |
| Ignore by default | `.git`, dependency dirs, build output, caches, and sensitive hidden dirs are skipped |
| Respect ignores | `.gitignore` and tool-specific ignore defaults should be honored where possible |
| Bounded output | Search results and file reads are capped before becoming model context |
| Cited ContextItem only | File results are injected as cited `project_file` or `project_search` ContextItems |
| Freshness visible | Indexed snippets carry stale markers when files change |
| Data, not instruction | Retrieved file text is treated as untrusted project data |

## Workflow Principles

Kira core is a graph runtime. A workflow skill may declare a graph like `planner -> gen_data -> send_kafka -> wait_ds -> reflect -> END`, but core must not know those node names. Core only understands generic graph loading, node execution, selected provider/model metadata, ToolNode dispatch, conditional edges, checkpointing, reliability policy, and event emission.

## Provider Principles

| Rule | Meaning |
| --- | --- |
| OpenAI-compatible first | Real provider integration uses the OpenAI-compatible API path |
| Fixture fallback | Local debug can continue without API keys by falling back to fixture when policy allows |
| Request over default | Request override beats skill hint, which beats configured default, which beats fixture fallback |
| Redacted everywhere | API keys never enter frontend, skill manifests, graph state, checkpoints, memory, or traces |
| Normalize once | Provider adapters map remote chunks to KiraEvents; later layers do not parse provider-specific chunks |

## Graph Reliability Principles

| Rule | Meaning |
| --- | --- |
| One runner per thread | A `thread_id` can have only one active executor |
| Replay is read-only | Debug replay does not repeat completed tools or side effects |
| Side effects are explicit | External actions use idempotency keys and ledger records |
| Retry by classification | Only retry known retryable, idempotent failures within bounded attempts |
| Repair is visible | Unknown or conflicted state pauses for user/developer repair instead of guessing |
