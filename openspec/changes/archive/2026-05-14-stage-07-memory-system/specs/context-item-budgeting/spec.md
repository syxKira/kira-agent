## ADDED Requirements

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
