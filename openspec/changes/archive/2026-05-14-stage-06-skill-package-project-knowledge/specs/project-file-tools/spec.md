## ADDED Requirements

### Requirement: Project knowledge reuses file tool policy

The project knowledge index and retrieval system SHALL reuse Stage 02 project root resolution, ignore, binary, large-file, symlink escape, and read-only policies.

#### Scenario: Retrieval honors path escape rejection
- **WHEN** project retrieval or indexing encounters a path that resolves outside the allowed root
- **THEN** it rejects or excludes that path with structured policy metadata and no file content

#### Scenario: Index excludes noisy directories
- **WHEN** project inventory scans ignored directories such as `.git`, dependency folders, build outputs, or caches
- **THEN** those files are not indexed as retrievable content

### Requirement: File tools remain separate from project retrieval

The system SHALL preserve direct Stage 02 list/search/read tools while adding project knowledge APIs and ContextItem retrieval.

#### Scenario: Direct read tool still works
- **WHEN** a workflow or user invokes `read_project_file`
- **THEN** the existing bounded read result shape remains available independent of project index state

#### Scenario: Retrieval does not add mutation tools
- **WHEN** project knowledge retrieval is enabled
- **THEN** no write, delete, patch, stage, format, or shell tool is added to the tool registry

