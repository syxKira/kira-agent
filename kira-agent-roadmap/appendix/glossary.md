# Appendix: Glossary

| Term | Meaning |
| --- | --- |
| Kira core | Backend runtime that loads skills, registers tools, compiles graphs, streams events, and manages state |
| Skill | Extension unit that can provide docs, tools, workflow definitions, and context injection rules |
| Skill manifest | Optional `skill.yaml` machine-readable contract for workflows, tools, permissions, context, UI metadata, and fixtures |
| Workflow skill | A skill that provides a LangGraph workflow factory or declaration |
| Business workflow | A domain-specific graph such as data generation, Kafka send, DS wait, and reflection |
| StateGraph | LangGraph graph used to define nodes and edges for workflow execution |
| ToolNode | LangGraph prebuilt node that dispatches `BaseTool` calls |
| ContextItem | Budgeted unit of model input such as skill, memory, project file, search result, or history |
| Conversation | Multi-turn chat/session container identified by `conversation_id` |
| Transcript | Ordered conversation record of visible user/assistant messages, bounded tool summaries, and control markers |
| Turn | One user request and the assistant work that answers it |
| Parent chain | Message ancestry used to reconstruct active conversation history |
| Active head | Message ID that future prompts continue from |
| Fork | New conversation created from a selected prior message/turn |
| Rollback | Non-destructive move of active head to an earlier message/turn |
| Conversation summary | Runtime-generated compact summary of older transcript turns used as bounded context |
| Compaction summary | Explicit transcript artifact summarizing an older message span with source range and stale flag |
| Tool summary | Bounded transcript/context representation of a tool result, distinct from raw tool output |
| Tool output replacement | Record that replaces large/sensitive raw tool output with a bounded stub, summary, hash, and optional local reference |
| Memory citation | Audit record created whenever a memory is injected into model context |
| Memory candidate | Proposed memory extracted from a completed run before approval or write |
| Project file context | Read-only local files and search snippets used as model context |
| Project knowledge retrieval | Inventory, chunking, search, ranking, citation, and ContextItem packing over allowed local files |
| Project inventory | Kira-owned metadata about allowed project files: path, size, mtime, hash, type, ignore reason |
| Project chunk | Stable text segment with path, byte/line range, chunk ID, and content hash |
| Project citation | Source metadata attached to a project ContextItem, including path, line range, chunk hash, indexed time, and stale flag |
| Controlled Python execution | Python script execution with cwd/env/timeout/output/audit/HITL boundaries |
| thread_id | Stable graph/run execution cursor used by checkpointer and resume |
| Checkpointer | Durable state saver used by LangGraph for resume and replay |
| Run lock | Per-`thread_id` ownership record that prevents duplicate active graph executors |
| Side-effect ledger | Kira-owned table that records idempotency keys, tool/action status, result hashes, and audit references |
| Idempotency key | Stable key used to prevent completed tool calls or external actions from repeating during resume/replay |
| Repair | User/developer-guided recovery path for failed or unknown workflow state |
| Interrupt | LangGraph mechanism for pausing a run and waiting for user input |
| KiraEvent | Backend-to-frontend event streamed over SSE |
| Session projection | UI-friendly view derived from checkpoints, events, and audit records |
| Fixture provider | Deterministic provider used for local tests and replay |
| DESIGN.md | Markdown design contract that captures visual tokens, component rules, layout principles, and screenshot checks for coding agents |
| Task rail | Workbench sidebar showing local runs/tasks, status, and quick new-task action |
