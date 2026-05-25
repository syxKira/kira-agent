## ADDED Requirements

### Requirement: Skill panel shows package catalog and details

The frontend SHALL provide a skill panel that shows skill catalog summaries, package source, active/shadowed status, permissions, workflows, model hints, fixtures, validation status, and detail loading state.

#### Scenario: Catalog renders without full docs
- **WHEN** the skill panel loads summary data
- **THEN** it renders skill names, descriptions, source, and status without requiring full `SKILL.md` body content

#### Scenario: Detail view shows manifest metadata
- **WHEN** the user opens a skill detail view
- **THEN** the panel shows workflows, tools, permissions, model hints, fixtures, references, validation warnings, and redacted metadata

### Requirement: Skill activation is explicit and inspectable

The frontend SHALL allow explicit skill activation and show which skill context will be loaded before a run.

#### Scenario: User activates skill
- **WHEN** the user selects an invocable skill
- **THEN** the workbench records the active skill and can show loaded ContextItems or loading errors

### Requirement: Project knowledge panel shows index status

The frontend SHALL provide a project knowledge panel showing root, index status, file count, chunk count, stale count, last refresh, refresh state, and policy omissions.

#### Scenario: Index status renders
- **WHEN** the frontend fetches project index status
- **THEN** it shows file/chunk counts, stale markers, last refresh time, and omitted counts

### Requirement: Project search results show citations

The frontend SHALL render project search results with source path, line range, snippet preview, chunk ID, stale marker, score, and omitted/truncated metadata.

#### Scenario: Search result citation is visible
- **WHEN** project search returns cited snippets
- **THEN** the project panel shows citations and stale status without exposing raw internal index rows

### Requirement: Run context inspector explains context usage

The frontend SHALL show run context traces including included, truncated, and omitted skill/project ContextItems and their trust labels.

#### Scenario: Context trace explains omissions
- **WHEN** context packing omits project snippets due to budget
- **THEN** the frontend can show which items were omitted and why

