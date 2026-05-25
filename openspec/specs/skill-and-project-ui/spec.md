# skill-and-project-ui Specification

## Purpose
TBD - created by archiving change stage-06-skill-package-project-knowledge. Update Purpose after archive.
## Requirements
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

### Requirement: Inspector surfaces follow the Stage 10 dark shell
The frontend SHALL render skill, project knowledge, memory, diagnostics, audit, trace, permission, and replacement inspection surfaces inside the Stage 10 dark inspector or responsive drawer without changing their data semantics.

#### Scenario: Inspector panels remain functionally equivalent
- **WHEN** the user opens skill, project knowledge, memory, diagnostics, audit, trace, permission, or replacement inspection surfaces
- **THEN** the frontend SHALL show the same existing frontend-safe data and actions in the Stage 10 visual shell
- **THEN** the UI SHALL preserve existing redaction, permission, no-secret, hidden-thinking, and bounded-output behavior

#### Scenario: Narrow viewport uses drawer behavior
- **WHEN** inspector surfaces are used at a narrow viewport width
- **THEN** the frontend SHALL move those surfaces behind drawer, tab, or sheet controls
- **THEN** the main timeline and composer SHALL remain the primary visible workflow

### Requirement: Skill and active workflow context is compact and inspectable
The frontend SHALL present skill catalog summaries, active skill state, workflow metadata, model hints, fixtures, validation status, and loaded ContextItems in compact Stage 10 panels.

#### Scenario: Active skill context is clear
- **WHEN** a skill is selected or active for a run
- **THEN** the inspector SHALL show skill name, source, status, workflow metadata, model hint or fixture metadata when available, validation warnings, and loaded or omitted ContextItems without requiring full `SKILL.md` body content by default

### Requirement: Project knowledge and context traces are visually cited
The frontend SHALL present project index status, search results, retrieval snippets, context inclusion, omissions, stale markers, and truncation metadata as cited Stage 10 cards or rows.

#### Scenario: Project result card is citeable
- **WHEN** project search or run context trace returns a cited project snippet
- **THEN** the frontend SHALL show path, line range or chunk ID when available, score or ranking metadata when available, stale status, omission/truncation reason when present, and a bounded snippet preview

#### Scenario: Context omission remains understandable
- **WHEN** skill, project, memory, transcript, compaction, replacement, or inactive-branch ContextItems are omitted from a run context
- **THEN** the inspector SHALL show item kind, trust label, omission or truncation reason, and relevant IDs without exposing raw hidden thinking, provider secrets, or raw replacement content

### Requirement: Supporting panels preserve keyboard and focus behavior
The frontend SHALL provide keyboard-reachable tabs, drawer controls, copy buttons, expanders, search/filter inputs, and action buttons for Stage 10 supporting panels.

#### Scenario: Keyboard user can inspect supporting panels
- **WHEN** a keyboard-only user navigates the Stage 10 inspector or drawer
- **THEN** focus order, accessible names, visible focus states, and escape or close behavior SHALL allow inspecting skills, project knowledge, memory, diagnostics, audit, and trace data without trapping focus

