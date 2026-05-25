## ADDED Requirements

### Requirement: Resolve project roots safely

The system SHALL resolve local file tool roots to canonical project roots and reject traversal or symlink escape.

#### Scenario: Path traversal is rejected

- **WHEN** a file tool request uses a path that resolves outside the allowed project root
- **THEN** the tool returns a structured permission error and no file content

#### Scenario: Symlink escape is rejected

- **WHEN** a file tool request follows a symlink that resolves outside the allowed project root
- **THEN** the tool returns a structured permission error and no file content

### Requirement: List project files

The system SHALL provide `list_project_files(root?, glob?, limit?)` as a read-only tool for bounded project file discovery.

#### Scenario: File list is bounded and relative

- **WHEN** the tool lists files in an allowed project root
- **THEN** it returns relative paths, stable root metadata, result count, omitted count, and truncation status within the requested or default limit

#### Scenario: Listing uses fallback without rg

- **WHEN** `rg` is unavailable
- **THEN** the tool uses the Python fallback and still applies root, ignore, and result cap policies

### Requirement: Search project files

The system SHALL provide `search_project_files(query, root?, glob?, limit?)` as a read-only tool for bounded text search.

#### Scenario: Search returns structured matches

- **WHEN** the tool searches for a query in an allowed project root
- **THEN** it returns relative path, line number, bounded preview text, file metadata, omitted count, and truncation status

#### Scenario: Search uses fallback without rg

- **WHEN** `rg` is unavailable
- **THEN** the tool uses the Python fallback and still applies root, ignore, binary, large-file, and result cap policies

### Requirement: Read project file slices

The system SHALL provide `read_project_file(path, offset?, limit?)` as a read-only tool for bounded text file reads.

#### Scenario: Read returns bounded text and metadata

- **WHEN** the tool reads an allowed text file
- **THEN** it returns bounded content plus path, root ID, file size, mtime, line or byte range, content hash when cheap, and truncation status

#### Scenario: Binary file is rejected

- **WHEN** the tool reads a binary file
- **THEN** it returns a structured binary-file error and no file content

#### Scenario: Oversized read is capped

- **WHEN** the requested read exceeds the configured output cap
- **THEN** the tool returns truncated content with metadata describing the applied cap

### Requirement: Ignore unsafe and noisy paths

The system SHALL ignore `.git`, dependency directories, build outputs, caches, and sensitive hidden directories by default, and SHALL respect `.gitignore` where practical.

#### Scenario: Ignored directories stay out of results

- **WHEN** listing or searching a project containing ignored directories
- **THEN** ignored files are omitted or reported with ignore metadata and are not returned as readable content

### Requirement: Keep file tools read-only

The system SHALL NOT write, move, delete, patch, format, stage, or otherwise mutate project files through Stage 02 file tools.

#### Scenario: File tools expose no write operation

- **WHEN** built-in file tools are registered
- **THEN** only list, search, and bounded read operations are available
