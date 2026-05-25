# memory-record-contract Specification

## Purpose
TBD - created by archiving change stage-07-memory-system. Update Purpose after archive.
## Requirements
### Requirement: Memory records are typed, scoped, and statused
The system SHALL store local memory records with stable IDs, scope, type, status, text, tags, confidence, source metadata, timestamps, optional expiration, and redacted public metadata.

#### Scenario: Manual memory validates required fields
- **WHEN** a client creates a memory record with valid scope, type, status, text, tags, confidence, and source metadata
- **THEN** the backend persists the record in Kira-owned storage and returns a frontend-safe payload

#### Scenario: Invalid memory shape is rejected
- **WHEN** a client creates a memory record with an unknown scope, unknown type, invalid confidence, missing text, or malformed source metadata
- **THEN** the backend rejects the request with a structured validation error and stores no memory record

### Requirement: Memory records are separate from transcript and project knowledge
The system SHALL NOT treat transcript history, skill documentation, project search results, or raw file snippets as memory unless a validated memory write explicitly creates a memory record.

#### Scenario: Project retrieval does not create memory
- **WHEN** a run retrieves project snippets through Stage 06 project knowledge
- **THEN** no memory record is created unless a separate memory write or approved candidate action occurs

#### Scenario: Transcript is not durable memory
- **WHEN** a run completes and extraction is disabled or dry-run only
- **THEN** the transcript remains outside the durable memory store

### Requirement: Memory secret guard runs before persistence
The system SHALL run a secret and sensitive-data guard before storing memory records, events, candidates, citations, or tombstones.

#### Scenario: API key is blocked
- **WHEN** memory text or source metadata includes an API key, authorization header, bearer token, cookie, private key, `.env` value, raw provider config, or unredacted provider error
- **THEN** the backend rejects or redacts the unsafe value before persistence and returns a structured guard result

#### Scenario: Rejected secret is not persisted
- **WHEN** the secret guard rejects a memory write
- **THEN** raw rejected text is absent from memory tables, run state, replay exports, diagnostics, and frontend responses

### Requirement: Memory events record changes without secrets
The system SHALL record memory creation, update, retrieval, injection, archive, delete, merge, refresh, stale, promote, and extraction events with redacted metadata.

#### Scenario: Update event is stored
- **WHEN** a memory record is updated
- **THEN** the backend stores a memory event identifying the action, memory ID, timestamp, redacted actor/source, and redacted summary

#### Scenario: Event metadata is redacted
- **WHEN** memory event metadata contains provider metadata or user-provided text
- **THEN** stored and public event payloads omit raw secrets and unbounded text

### Requirement: Memory schemas are shared
The system SHALL publish shared schemas for memory records, memory sources, memory events, memory candidates, memory citations, memory retrieval explanations, memory actions, and memory API responses.

#### Scenario: Frontend validates memory response shape
- **WHEN** the frontend fetches memory records or candidates
- **THEN** the payload conforms to the shared memory schemas and contains no raw provider secrets

