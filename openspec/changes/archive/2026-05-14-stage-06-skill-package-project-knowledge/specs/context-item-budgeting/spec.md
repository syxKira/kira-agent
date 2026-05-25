## ADDED Requirements

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

