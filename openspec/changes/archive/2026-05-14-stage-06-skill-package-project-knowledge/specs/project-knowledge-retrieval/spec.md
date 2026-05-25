## ADDED Requirements

### Requirement: Retrieval combines live and indexed lexical candidates

The system SHALL retrieve project snippets using a combination of live `rg` candidates, indexed FTS candidates when available, explicit path filters, active skill hints, and recent run context.

#### Scenario: Search returns ranked snippets
- **WHEN** a user or run requests project retrieval for a query
- **THEN** the retriever returns ranked snippets with source metadata, scores, and omission counts

#### Scenario: rg fallback works without index hit
- **WHEN** the index is stale or FTS is unavailable
- **THEN** live lexical search can still return bounded cited results through the same policy layer

### Requirement: Citations identify source and freshness

The system SHALL attach citations with root ID, relative path, line range, chunk ID, content hash, indexed-at time, stale flag, and retrieval query metadata.

#### Scenario: Citation includes line range
- **WHEN** retrieval returns a project snippet
- **THEN** the citation identifies the relative source path and start/end lines when known

#### Scenario: Stale citation is visible
- **WHEN** the underlying file has changed since the snippet was indexed
- **THEN** retrieval or context trace marks the citation as stale

### Requirement: Retrieval results pack into ContextItems

The system SHALL convert selected retrieval results into `project_file` or `project_search` ContextItems with citations, trust labels, and budget metadata.

#### Scenario: Retrieval context is injected into run
- **WHEN** a run opts into project context
- **THEN** selected retrieval snippets are packed as ContextItems before provider input assembly

### Requirement: Project knowledge APIs are local and read-only

The system SHALL expose local project index, refresh, search, file, and run context APIs that reuse project file policy and return frontend-safe payloads.

#### Scenario: Search API returns citations
- **WHEN** the frontend calls project search
- **THEN** the response includes ranked results, citations, stale markers, omitted counts, and no raw provider secrets

#### Scenario: File API remains read-only
- **WHEN** the frontend reads a project file through project knowledge API
- **THEN** the backend returns a bounded read with citation metadata and does not mutate the project

### Requirement: Prompt injection fixtures are covered

The system SHALL include adversarial project file fixtures proving retrieved content remains untrusted data and cannot grant permissions.

#### Scenario: Adversarial file cannot expand tools
- **WHEN** retrieval selects a file containing instructions to enable forbidden tools
- **THEN** the run context marks the snippet as project data and effective permissions remain unchanged

