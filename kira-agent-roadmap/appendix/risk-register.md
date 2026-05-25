# Appendix: Risk Register

| Risk | Impact | Mitigation | Roadmap Home |
| --- | --- | --- | --- |
| Core accidentally grows business workflow logic | Skills become less portable and Kira becomes domain-specific | Keep workflow node names and graph semantics inside skills; test with generic skill graph | Stage 03 |
| File retrieval becomes file mutation | Kira drifts back into code-agent behavior | Provide only list/search/read tools; no write/edit/patch APIs | Stage 02 |
| Python execution becomes general shell | Security and audit risk | No shell expansion; cwd/env/timeout/output caps; approval for risky scripts | Stage 02, Stage 09 |
| LangChain dependency expands quietly | Architecture becomes hard to reason about | Document allowed LangChain APIs and test imports/usage boundaries | Stage 02 |
| Provider config leaks secrets | API keys can appear in UI, traces, checkpoints, memory, or skill manifests | Central redaction, provider boundary, no raw keys in graph state, doctor uses key presence only | Real LLM provider change, Stage 09 |
| Provider retry conflicts with graph retry | A failed model call is retried too many times or repeats side effects | Define provider retry boundary and record provider attempts separately from graph attempts | Stage 04 |
| Fixture fallback hides missing real config | Local runs appear successful but do not exercise the real model | Surface fallback status in provider readiness, run metadata, audit, and smoke-test docs | Real LLM provider change, Stage 09 |
| LangGraph events leak implementation details to frontend | Frontend becomes coupled to LangGraph internals | Map `astream_events` to KiraEvent before SSE | Stage 05 |
| Checkpoint and UI state diverge | Resume/replay becomes unreliable | Treat checkpointer as authority and session projection as derived | Stage 04 |
| Duplicate resume starts two graph runners | External actions can run twice and state becomes inconsistent | Per-`thread_id` run lock, heartbeat, duplicate resume conflict, side-effect ledger | Stage 04 |
| Side effects repeat during replay/resume | Remote systems receive duplicate sends or writes | Stable idempotency keys, ledger before/after side effects, replay is read-only by default | Stage 04 |
| Retry policy hides real failures | Runs loop or mask permission/validation bugs | Error taxonomy, bounded attempts, non-retryable classes, visible retry events | Stage 04 |
| Event ordering is unstable across SSE reconnect | Frontend timeline and replay disagree | Persist KiraEvents with monotonic sequence numbers per run | Stage 04, Stage 05 |
| Local search floods prompt | Model context becomes noisy and expensive | Project retrieval index, ranking, citations, ContextItem budget, included/omitted trace | Stage 06 |
| Retrieved file content injects instructions | Local docs can manipulate tool use or policy | Label project snippets as untrusted data, preserve instruction hierarchy, require HITL for risky actions | Stage 06, Stage 09 |
| Project index becomes stale | Agent answers from old file content | mtime/size/hash checks, stale citation flags, refresh before retrieval within caps | Stage 06 |
| Skills load too much content | Slow runs and prompt pollution | Frontmatter catalog first; progressive load only activated skills | Stage 06 |
| Skill permissions are ambiguous | A skill may silently gain unsafe tools/actions | Two-layer permission model: invocation permission plus tool/action permission | Stage 06, Stage 09 |
| Workflow skill has no regression surface | Skill workflows break silently | Require fixtures for workflow skills and validate manifests | Stage 06 |
| Memory stores temporary or wrong facts | Agent behavior drifts and users lose trust | Typed scopes, dry-run extraction, citations, lifecycle, explain/delete | Stage 07 |
| Secrets enter memory, audit, or trace | Privacy and credential exposure | Secret guard before memory writes; redaction before persistence/export | Stage 07, Stage 09 |
| Follow-up prompts lose prior context | Kira behaves like isolated one-shot calls instead of a Web Agent | Stage 08 conversation transcript, recent-history ContextItems, rolling summary, conversation ID in run requests | Stage 08 |
| Transcript is mistaken for memory | Temporary dialogue becomes durable behavior without user control | Keep transcript conversation-scoped; Stage 07 memory writes require explicit policy/HITL | Stage 08 |
| Hidden thinking leaks through transcript | Private reasoning appears in UI or future model context | Persist visible text only; store thinking as debug/status metadata, never as assistant history | Stage 08, Stage 09 |
| Conversation history floods prompt | Long chats exceed budget or bury current task | Recent raw window, rolling summaries, bounded tool summaries, included/omitted context trace | Stage 08 |
| Transcript crosses conversation boundaries | One user's/task's context contaminates another local session | `conversation_id` isolation tests and storage foreign-key style checks | Stage 08 |
| Rollback keeps using abandoned messages | Agent answers from messages the user thought were discarded | Active parent chain and active head drive context; inactive branches appear only in trace | Stage 08 |
| Fork loses provenance | Debugging or memory extraction cannot explain where a branch came from | Store fork source conversation/message/turn and logical parent IDs | Stage 08 |
| Compaction silently rewrites history | Users cannot inspect why context changed | Explicit compaction artifacts with source ranges, hashes, token estimates, and stale flags | Stage 08 |
| Tool output replacement hides important evidence | Agent loses critical details or debug export becomes misleading | Store summary, hash, omitted count, retention reason, and context trace; gated raw retrieval in Stage 09 | Stage 08, Stage 09 |
| Missing `rg` breaks local retrieval | Poor local portability | Python fallback and doctor warning | Stage 02, Stage 09 |
| UI polish hides runtime truth | Users may mistake thinking, fixture data, retries, or tool previews for final answers/actions | Stage 10 event-specific blocks, visible state labels, hidden-thinking boundary, screenshot tests | Stage 10 |
| Dark UI becomes low contrast or cramped | Long local runs and tool outputs become hard to read | Design tokens, contrast checks, responsive screenshots, stable card dimensions | Stage 10 |
