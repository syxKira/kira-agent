# 01 Kai Capability Map

This map records which parts of Kai's roadmap transfer into Kira, which are adapted, and which are rejected.

## Transfer Matrix

| Kai area | Kira decision | Roadmap home |
| --- | --- | --- |
| Model/provider config | Reuse concept, implement in Python; later stages consume redacted provider/model metadata only | Stage 01, focused real LLM provider change, Stage 03+ |
| Fixture provider | Reuse for deterministic tests | Stage 01 |
| Streaming event protocol | Reuse visible text/thinking/tool event split | Stage 01, Stage 05 |
| Tool protocol | Adapt to `langchain-core` `BaseTool` | Stage 02 |
| Tool result formatting | Reuse normalized success/error/output cap idea | Stage 02 |
| Local grep/glob/read | Adapt first as read-only project context tools, then as project knowledge retrieval | Stage 02, Stage 06 |
| Bash | Reject general shell; replace with controlled Python script execution | Stage 02, Stage 09 |
| Middleware pipeline | Adapt through graph/runtime hooks and tool wrappers | Stage 03 |
| Plan mode | Do not port as a built-in profile; planning can be a skill workflow | Stage 03 |
| Session persistence | Adapt to LangGraph SQLite checkpointer plus session projection, event log, run lock, and side-effect ledger | Stage 04 |
| HITL manager | Adapt to `interrupt`, resume API, and frontend prompts | Stage 05 |
| Context Kernel | Reuse ContextItem and budget debug concepts | Stage 06 |
| Skills | Expand Kai Stage 10 into Web skill package contract with workflow/tool/context/UI/test metadata | Stage 03, Stage 06 |
| Memory system | Port Kai Stage 13 memory model rather than stopping at manual v0 | Stage 07 |
| Sub-agent | Defer; skills and graph nodes cover v0 extensibility | Risk register |
| Permission engine | Narrow to file read, Python execution, skill workflow actions, transcript operations, and memory writes | Stage 09 |
| Context quality eval | Reuse trace/replay idea after dogfooding | Stage 09 |

## Public Interface Mapping

| Kai interface | Kira interface |
| --- | --- |
| `ToolDef` | `BaseTool` / `@tool` |
| `UiEvent` | `KiraEvent` streamed over SSE |
| `PromptSubmission` | `POST /api/runs` input and skill/run metadata |
| `HumanInteractionManager` | LangGraph `interrupt` plus `POST /resume` |
| `SessionStore` | SQLite checkpointer plus session projection tables |
| `ContextItem` | Same concept, Python data model |
| `CommandRegistry` | Frontend command palette plus backend skill catalog |

## Reference Notes

- LangChain Core tools are used only for tool definitions, schemas, and validation.
- Provider config follows Kai's OpenAI-compatible preset idea, but later runtime state stores only redacted provider profile/model metadata and fixture fallback status.
- LangGraph `ToolNode` replaces a hand-written tool router for model/tool dispatch inside graph workflows.
- LangGraph checkpointing is the durable state source for graph resume; Kira adds run locks, event sequencing, idempotency keys, side-effect ledger, and failure taxonomy around it.
- The local file retrieval design intentionally borrows Kai's `rg`-first search discipline while excluding mutation tools; Kira then adds inventory, chunking, citations, freshness checks, and ContextItem packing.
- Skill packaging borrows Kai Stage 10 discovery/catalog/progressive loading, Claude-style rich frontmatter and permissions, and Codex-style concise package anatomy.
- Memory borrows Kai Stage 13 typed/scoped/cited lifecycle model, adapted to Kira's Web API and UI.
