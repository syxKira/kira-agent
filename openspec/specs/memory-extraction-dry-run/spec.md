# memory-extraction-dry-run Specification

## Purpose
TBD - created by archiving change stage-07-memory-system. Update Purpose after archive.
## Requirements
### Requirement: Post-run extraction defaults to dry-run
The system SHALL produce memory extraction candidates from completed runs without automatically writing memory records by default.

#### Scenario: Dry-run produces candidates
- **WHEN** a completed run is eligible for memory extraction
- **THEN** the backend returns candidate memories with suggested scope, type, text, confidence, source, reason, risk, dedupe metadata, and guard status

#### Scenario: Dry-run does not write memory
- **WHEN** extraction runs in dry-run mode
- **THEN** no memory record is created unless a later explicit approval or write action occurs

### Requirement: Extraction uses safe provider fallback
The system SHALL use deterministic fixture/mock extraction for tests and no-key local runs, and SHALL use the real provider only when configured and requested by policy.

#### Scenario: Missing key uses fixture extraction
- **WHEN** extraction is requested without valid real provider credentials
- **THEN** extraction completes through deterministic fixture/mock behavior or returns a structured skipped status

#### Scenario: Real extraction is skipped by default tests
- **WHEN** automated tests run without provider credentials
- **THEN** no test requires a real API key and real extraction smoke tests are skipped

### Requirement: Extraction applies secret guard and dedupe
The system SHALL run secret/sensitive guard and dedupe checks before persisting extraction candidates or allowing candidate approval.

#### Scenario: Secret candidate is blocked
- **WHEN** extraction output contains an API key, token, cookie, private key, `.env` value, raw provider config, or unredacted provider error
- **THEN** the candidate is marked blocked and raw unsafe text is not persisted

#### Scenario: Existing memory is detected
- **WHEN** an extracted candidate duplicates an active memory
- **THEN** the candidate is marked duplicate with matching memory IDs and is not recommended for direct write

### Requirement: Extraction sources are bounded and redacted
The system SHALL build extraction input from bounded run summaries, user feedback, selected skill metadata, workflow outcome, tool summaries, and redacted provider metadata.

#### Scenario: Raw transcript is not stored as candidate source
- **WHEN** extraction records candidate provenance
- **THEN** it stores bounded redacted summaries and references, not unbounded transcript text or raw provider payloads

### Requirement: Candidate review supports approval workflow
The system SHALL allow users to approve, reject, edit, or defer extraction candidates through API and UI without writing unapproved candidates as active memory.

#### Scenario: Approved candidate becomes memory
- **WHEN** a user approves a safe candidate with valid scope and type
- **THEN** the backend creates a memory record, links it to candidate provenance, and records memory events

