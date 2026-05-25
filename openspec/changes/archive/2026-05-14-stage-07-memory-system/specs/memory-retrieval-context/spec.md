## ADDED Requirements

### Requirement: Memory retrieval is deterministic and explainable
The system SHALL retrieve memory records with deterministic lexical scoring based on query overlap, scope match, type match, tags, confidence, recency, and prior usefulness.

#### Scenario: Search returns score reasons
- **WHEN** a client searches memory with a query and filters
- **THEN** the backend returns ranked memory results with scores, score reasons, matched fields, and omission counts

#### Scenario: Same fixture query is stable
- **WHEN** the same fixture memory set is searched with the same query and filters
- **THEN** result order and score reasons are deterministic

### Requirement: Memory retrieval respects scope and status
The system SHALL inject only in-scope `active` memories by default and SHALL exclude archived, deleted, stale, expired, or out-of-scope memories unless explicitly requested for inspection.

#### Scenario: Archived memory is not injected
- **WHEN** a memory record has status `archived`
- **THEN** run memory retrieval excludes it from provider context by default

#### Scenario: Wider scope requires matching context
- **WHEN** a run has project-local context
- **THEN** retrieval may include matching `session` and `projectLocal` memories but does not include unrelated project memories

### Requirement: Memory retrieval deduplicates results
The system SHALL deduplicate semantically equivalent or merged memory records before injection and SHALL expose dedupe metadata in retrieval explanations.

#### Scenario: Duplicate memories collapse
- **WHEN** two active memories have matching normalized text or a merge relationship
- **THEN** retrieval returns one injectable result and records omitted duplicate IDs in explanation metadata

### Requirement: Memory injection creates ContextItems and citations
The system SHALL convert selected memory retrieval results into `ContextItem(kind="memory")` records with memory citations and budget metadata.

#### Scenario: Memory context is injected into run
- **WHEN** a run opts into memory retrieval
- **THEN** selected memories are packed as ContextItems before provider input assembly
- **THEN** each included memory has a citation record linked to the run and memory ID

### Requirement: Memory retrieval is inspectable in run context traces
The system SHALL expose included, truncated, and omitted memory ContextItems and retrieval explanations in frontend-safe run context traces.

#### Scenario: Context trace includes memory reasons
- **WHEN** a run context trace includes memory ContextItems
- **THEN** the trace shows memory ID, scope, type, citation ID, score, score reasons, trust label, budget cost, and omission reasons without secrets
