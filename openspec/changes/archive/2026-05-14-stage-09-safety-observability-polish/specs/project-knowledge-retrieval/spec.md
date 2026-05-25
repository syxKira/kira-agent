## ADDED Requirements

### Requirement: Retrieval actions are permission-aware and audited
Project indexing, live search, FTS search, and file reads used for retrieval SHALL record permission decisions and audit metadata for root, path, ignored/sensitive status, stale markers, citation IDs, and omission reasons.

#### Scenario: Ignored or sensitive file omitted
- **WHEN** retrieval encounters ignored, binary, oversized, symlink-escaped, or sensitive files
- **THEN** the trace and audit output SHALL include redacted omission metadata and SHALL NOT inject omitted file content into provider context

### Requirement: Retrieval diagnostics explain index health
Doctor and trace export SHALL report project index health, stale files, skipped files, omitted snippets, no-`rg` fallback, citation quality, and prompt-injection fixture coverage.

#### Scenario: rg unavailable
- **WHEN** `rg` is not available locally
- **THEN** doctor SHALL warn about fallback behavior and retrieval SHALL continue with the safe Python fallback when possible
