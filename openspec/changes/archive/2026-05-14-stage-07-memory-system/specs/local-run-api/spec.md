## ADDED Requirements

### Requirement: Runs accept memory retrieval controls
The run creation API SHALL accept frontend-safe controls for optional memory retrieval, scope filters, type filters, top-k limits, and memory budget controls.

#### Scenario: Run opts into memory retrieval
- **WHEN** a run request includes memory retrieval controls
- **THEN** the backend retrieves eligible active memories, converts them into ContextItems, and includes them before provider input assembly

#### Scenario: Memory retrieval controls are redacted
- **WHEN** run creation returns metadata for memory context
- **THEN** the response omits raw memory secrets, raw provider secrets, and unbounded memory text

### Requirement: Run context trace exposes memory usage
The run context trace API SHALL show included, truncated, and omitted memory ContextItems, memory citations, and retrieval explanations.

#### Scenario: Context trace returns memory citations
- **WHEN** a client requests context trace for a run that injected memory
- **THEN** the response includes memory IDs, citation IDs, scopes, types, score reasons, trust labels, budget costs, and omission reasons

### Requirement: Memory APIs are local and bounded
The system SHALL expose local memory list, read, create, update, search, candidate, and action APIs with bounded payloads and redacted metadata.

#### Scenario: Memory search API returns explanations
- **WHEN** the frontend calls memory search
- **THEN** the response includes ranked memories, explanations, citations when applicable, omitted counts, and no raw provider secrets

#### Scenario: Unknown memory returns not found
- **WHEN** a client requests or acts on an unknown memory ID
- **THEN** the backend returns a structured not-found error and mutates no memory state
