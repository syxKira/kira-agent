## ADDED Requirements

### Requirement: Transcript stores compaction parts safely
The system SHALL store compaction summary transcript artifacts as bounded, redacted, non-answer parts or system messages without changing visible assistant answer text.

#### Scenario: Compaction appears in transcript metadata
- **WHEN** a conversation is compacted
- **THEN** the transcript can expose a frontend-safe compaction artifact with summary text, source range, status, and timestamps
- **THEN** it does not appear as if the assistant visibly answered with that summary

### Requirement: Transcript stores replacement parts safely
The system SHALL store tool-output replacement transcript artifacts as bounded, redacted summary or stub parts linked to the source tool result.

#### Scenario: Replacement part is not visible assistant answer
- **WHEN** a tool output is replaced
- **THEN** the transcript stores a replacement or tool summary part with replacement metadata
- **THEN** restored assistant answer text excludes raw replaced output and excludes replacement internals

### Requirement: Transcript APIs expose summary and replacement metadata
The system SHALL expose frontend-safe compaction and replacement metadata through transcript APIs without exposing raw provider secrets, hidden thinking, or raw replacement blobs.

#### Scenario: Transcript includes compaction metadata
- **WHEN** a client reads a conversation transcript after compaction
- **THEN** the response includes summary IDs, source ranges, stale status, and bounded summary text
- **THEN** the response does not include raw hidden thinking or provider secrets

#### Scenario: Transcript includes replacement metadata
- **WHEN** a client reads a conversation transcript with replaced tool output
- **THEN** the response includes replacement ID, reason, omitted count, hash or hash prefix, retention policy, and bounded summary
- **THEN** raw replaced content is not exposed
