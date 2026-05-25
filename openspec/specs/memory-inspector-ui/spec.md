# memory-inspector-ui Specification

## Purpose
TBD - created by archiving change stage-07-memory-system. Update Purpose after archive.
## Requirements
### Requirement: Memory inspector lists and filters records
The frontend SHALL provide a memory inspector that lists memory records with scope, type, status, tags, confidence, source summary, last used time, and lifecycle actions.

#### Scenario: Memory list renders
- **WHEN** the frontend fetches memory records
- **THEN** it renders records with scope, type, status, confidence, tags, and redacted source metadata

#### Scenario: Filters update results
- **WHEN** the user filters by scope, type, status, tag, or query
- **THEN** the memory list updates using backend memory search results and shows empty/error states

### Requirement: Memory inspector explains retrieval
The frontend SHALL show retrieval explanations including scores, score reasons, matched fields, citations, dedupe omissions, and budget omissions.

#### Scenario: Explain view shows reasons
- **WHEN** the user opens explanation for a memory search result
- **THEN** the UI shows score reasons, matched fields, citation metadata, and any omitted duplicate or budgeted-out memories

### Requirement: Memory inspector supports manual writes and lifecycle
The frontend SHALL allow users to add, edit, archive, delete, merge, refresh, stale, and promote memory records through backend APIs.

#### Scenario: Add memory form validates
- **WHEN** the user submits a manual memory with invalid scope/type/text
- **THEN** the UI shows validation feedback and does not show the memory as saved

#### Scenario: Lifecycle action updates list
- **WHEN** the user archives or deletes a memory
- **THEN** the UI updates the record status or removes it from active default views

### Requirement: Memory inspector reviews extraction candidates
The frontend SHALL show post-run extraction dry-run candidates with reason, confidence, risk, guard status, dedupe status, and approve/reject/edit actions.

#### Scenario: Candidate review blocks unsafe write
- **WHEN** a candidate is blocked by secret guard
- **THEN** the UI shows blocked status and does not offer direct approval as an active memory

### Requirement: Memory UI never exposes secrets
The frontend SHALL NOT render raw API keys, tokens, cookies, private keys, raw provider config, or unredacted provider errors from memory APIs.

#### Scenario: Redacted payload stays redacted
- **WHEN** memory API payloads include redacted provider/source metadata
- **THEN** the inspector displays only redacted metadata and raw secrets are absent from the DOM

