# context-item-budgeting Specification

## Purpose
TBD - created by archiving change stage-06-skill-package-project-knowledge. Update Purpose after archive.
## Requirements
### Requirement: ContextItems are typed and bounded

The system SHALL represent skill, workflow, permission, project file, project search, omission, and debug context as typed ContextItems with stable IDs, kind, text or payload, metadata, trust label, and estimated budget cost.

#### Scenario: Skill doc becomes ContextItem
- **WHEN** an activated skill loads its `SKILL.md` body
- **THEN** the loaded content is emitted as one or more bounded `skill_doc` ContextItems with source metadata

#### Scenario: Project snippet becomes ContextItem
- **WHEN** project retrieval selects a snippet
- **THEN** the snippet is emitted as a `project_file` or `project_search` ContextItem with citation metadata and trust label

### Requirement: Context budget packing records inclusion decisions

The system SHALL pack ContextItems into a run budget and record included, truncated, and omitted items with reasons.

#### Scenario: Budget omits overflow
- **WHEN** selected ContextItems exceed the configured budget
- **THEN** the packer includes higher-ranked items, truncates where allowed, and records omitted item IDs and reasons

#### Scenario: Context trace is inspectable
- **WHEN** a run is created with skill or project context
- **THEN** a frontend-safe context trace exposes included, truncated, and omitted ContextItems without raw provider secrets

### Requirement: Retrieved local content is untrusted data

The system SHALL label retrieved project content as untrusted project data and SHALL keep it separate from system, developer, and user instructions during provider input assembly.

#### Scenario: Project instructions cannot grant permission
- **WHEN** retrieved project text contains instructions to use extra tools or reveal secrets
- **THEN** the content remains data-only ContextItem text and does not alter effective tool permissions or provider config

### Requirement: ContextItem schemas are shared

The system SHALL publish shared schemas for ContextItems, context traces, project citation metadata, and budget omission metadata.

#### Scenario: Frontend renders context trace from shared contract
- **WHEN** the frontend fetches a run context trace
- **THEN** the payload validates against shared schemas and can show source, trust, budget, included, truncated, and omitted metadata

### Requirement: Memory ContextItems are supported
The system SHALL represent selected memory records as typed `memory` ContextItems with stable IDs, text, metadata, trust label, citations, and estimated budget cost.

#### Scenario: Memory record becomes ContextItem
- **WHEN** memory retrieval selects an active memory for a run
- **THEN** the selected memory is emitted as a bounded `memory` ContextItem with source and retrieval metadata

### Requirement: Memory budget decisions are traced
The system SHALL include memory ContextItems in the existing context budget packer and record included, truncated, and omitted memory items with reasons.

#### Scenario: Memory omitted by budget
- **WHEN** selected memory ContextItems exceed the configured budget
- **THEN** the context trace records omitted memory IDs, kinds, score metadata, and budget reasons

### Requirement: Memory citations remain distinct from project citations
The system SHALL keep memory citations distinct from project file citations while exposing both through run context traces.

#### Scenario: Trace contains mixed citations
- **WHEN** a run uses both project retrieval and memory retrieval
- **THEN** the context trace identifies project citations and memory citations separately without merging their provenance

### Requirement: Conversation ContextItems are supported
The system SHALL represent transcript-derived context as typed ContextItems with stable IDs, text, metadata, trust label, citations or transcript references, and estimated budget cost.

#### Scenario: User transcript becomes ContextItem
- **WHEN** the context builder selects a prior visible user message
- **THEN** it emits a `conversation_history` ContextItem with conversation ID, turn ID, message ID, role, trust label, and budget cost

#### Scenario: Tool summary becomes ContextItem
- **WHEN** the context builder selects a prior bounded tool summary
- **THEN** it emits a `tool_summary` ContextItem with tool name, status, source message/part IDs, and budget cost

### Requirement: Conversation ContextItems are packed with other context
The system SHALL pack conversation history alongside skill, project, and memory ContextItems using deterministic priority and budget rules.

#### Scenario: Mixed context trace
- **WHEN** a run uses conversation history, project retrieval, and memory retrieval
- **THEN** the context trace identifies each ContextItem kind separately
- **THEN** omission and truncation records preserve the source kind and IDs

### Requirement: Transcript omission metadata is inspectable
The system SHALL record why transcript ContextItems were included, truncated, or omitted.

#### Scenario: Old history is omitted
- **WHEN** the context budget cannot include all eligible transcript messages
- **THEN** the trace records omitted message IDs, turn IDs, item kind, reason, and estimated budget cost

### Requirement: Summary ContextItems are supported
The system SHALL represent transcript summaries as typed `conversation_summary` and `compaction_summary` ContextItems with stable IDs, bounded text, metadata, trust label, transcript references, and estimated budget cost.

#### Scenario: Compaction summary becomes ContextItem
- **WHEN** the context builder selects a non-stale compaction summary
- **THEN** it emits a `compaction_summary` ContextItem with conversation ID, summary ID, source message range, source turn range, tail boundary, stale status, trust label, and budget cost

#### Scenario: Conversation summary becomes ContextItem
- **WHEN** the context builder selects a rolling conversation summary
- **THEN** it emits a `conversation_summary` ContextItem with summary ID, covered source IDs, summarizer metadata, trust label, and budget cost

### Requirement: Summary ContextItems have deterministic budget priority
The system SHALL pack compaction and conversation summary ContextItems with deterministic priority relative to recent conversation history, tool summaries, project context, memory, and skill context.

#### Scenario: Summary preserves older context under budget
- **WHEN** a conversation has old summarized history and recent raw tail messages
- **THEN** the budget packer can include the summary before lower-value old raw messages
- **THEN** inclusion and omission decisions are stable for identical inputs

### Requirement: Replacement metadata is traceable in budget decisions
The system SHALL record replacement stub budget decisions with replacement IDs, source part IDs, reasons, omitted counts, and budget costs.

#### Scenario: Replacement stub is truncated
- **WHEN** a replacement stub text exceeds per-item budget
- **THEN** the context packer truncates or omits it according to budget rules
- **THEN** the trace records replacement ID, truncation or omission reason, and budget cost

### Requirement: Shared schemas include summary and replacement context
The system SHALL publish shared schemas for compaction summaries, replacement records, summary ContextItems, replacement trace metadata, and Stage 08b examples.

#### Scenario: Frontend validates summary trace
- **WHEN** the frontend fetches a run context trace containing compaction and replacement metadata
- **THEN** the payload validates against shared schemas
- **THEN** the frontend can render item kind, source IDs, stale status, replacement reason, and budget metadata without raw secrets

