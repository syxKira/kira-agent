# project-knowledge-index Specification

## Purpose
TBD - created by archiving change stage-06-skill-package-project-knowledge. Update Purpose after archive.
## Requirements
### Requirement: Project inventory respects file policy

The system SHALL inventory project files only through the existing safe root, ignore, symlink, binary, large-file, and read-only policies.

#### Scenario: Symlink escape is excluded
- **WHEN** project inventory encounters a symlink that resolves outside the allowed root
- **THEN** it excludes the file and records the exclusion reason without reading content

#### Scenario: Ignored directories are excluded
- **WHEN** project inventory scans `.git`, dependency directories, build outputs, caches, or ignored paths
- **THEN** those paths are omitted or recorded as ignored and are not indexed as readable content

### Requirement: Project files are chunked with stable identifiers

The system SHALL chunk readable text files into stable chunks with root ID, relative path, byte range, line range, content hash, language/type hint, and chunk ID.

#### Scenario: Unchanged chunk ID is stable
- **WHEN** a file is re-indexed without content changes
- **THEN** unchanged chunks retain stable chunk IDs

#### Scenario: Changed file produces stale markers
- **WHEN** a file changes after indexing
- **THEN** existing citations for old chunks can be marked stale until refresh updates them

### Requirement: Project index stores metadata in Kira-owned SQLite

The system SHALL store project root, file, chunk, FTS, retrieval, citation, and index status records only in Kira-owned SQLite/cache storage.

#### Scenario: Index writes do not mutate project files
- **WHEN** project indexing refreshes inventory and chunks
- **THEN** it writes only to Kira-owned storage and does not write, move, delete, patch, format, or stage project files

### Requirement: Incremental refresh is capped

The system SHALL refresh project inventory and index incrementally within configurable file-count, byte, and time caps.

#### Scenario: Large project refresh is bounded
- **WHEN** a project contains more files than the configured cap
- **THEN** refresh processes a bounded subset and records omitted counts and truncation metadata

### Requirement: FTS is optional with safe fallback

The system SHALL use SQLite FTS5 when available and SHALL fall back to metadata-only indexing plus live lexical search when FTS5 is unavailable.

#### Scenario: FTS unavailable still indexes metadata
- **WHEN** SQLite FTS5 is unavailable
- **THEN** project index refresh still stores file/chunk metadata and project search can use live fallback search

