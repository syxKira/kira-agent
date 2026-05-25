# skill-package-contract Specification

## Purpose
TBD - created by archiving change stage-06-skill-package-project-knowledge. Update Purpose after archive.
## Requirements
### Requirement: Skill packages expose required SKILL markdown

The system SHALL require each local skill package to include `SKILL.md` with valid frontmatter containing at least `name` and `description`.

#### Scenario: SKILL markdown summary is cataloged
- **WHEN** a local skill directory contains valid `SKILL.md` frontmatter
- **THEN** the skill catalog includes the skill name, description, source, and invocation metadata without loading the full body

#### Scenario: Missing SKILL markdown is rejected
- **WHEN** a local skill directory does not contain `SKILL.md`
- **THEN** the package validator marks the skill invalid and excludes it from invocable catalog results

### Requirement: Skill manifests validate package metadata

The system SHALL validate optional `skill.yaml` manifests for workflows, tools, context hints, permissions, UI metadata, fixtures, dependencies, and model hints.

#### Scenario: Workflow skill requires manifest
- **WHEN** a skill package declares workflows, tools, fixtures, or permission policy
- **THEN** the package validator requires a valid `skill.yaml`

#### Scenario: Secret-like manifest fields are rejected
- **WHEN** a manifest attempts to declare API keys, authorization headers, raw provider config, or custom base URLs
- **THEN** validation fails or removes the secret-like fields before public metadata, graph state, or context traces are produced

### Requirement: Discover skills from multiple local directories

The system SHALL discover local skill packages from configured bundled, project-local, and user-local directories with deterministic source priority.

#### Scenario: Multiple directories are scanned
- **WHEN** skill discovery runs
- **THEN** it scans enabled skill roots, records source metadata, and reports valid and invalid packages

#### Scenario: Duplicate skills resolve by priority
- **WHEN** two discovered packages declare the same skill ID
- **THEN** the highest-priority valid package becomes active and shadowed packages remain inspectable as non-active entries

### Requirement: Progressive skill loading is enforced

The system SHALL load only skill summary metadata during catalog discovery and load full `SKILL.md` body, references, and assets only after explicit activation, validated auto route, or workflow-owned context need.

#### Scenario: Catalog request avoids full body load
- **WHEN** the frontend requests skill catalog summary
- **THEN** the backend returns summary metadata without full instruction body or reference contents

#### Scenario: Explicit activation loads context
- **WHEN** a user explicitly activates a skill
- **THEN** the backend loads the skill body and selected references as bounded ContextItems

### Requirement: Skill permissions narrow core policy

The system SHALL enforce skill invocation, tool, action, workflow, and model-hint permissions as narrowing constraints on top of Kira core policy.

#### Scenario: Skill cannot expand tool policy
- **WHEN** a skill manifest allows a tool that core policy does not allow
- **THEN** the effective permission set excludes that tool and records a validation or policy warning

#### Scenario: Skill-provided Python uses controlled execution
- **WHEN** a skill references Python scripts or Python-backed tools
- **THEN** execution goes through controlled Python execution and never through a general shell

### Requirement: Skill fixtures validate packages

The system SHALL support package fixtures that can validate manifests, workflows, permissions, context loading, and fixture-provider runs without requiring a real API key by default.

#### Scenario: Fixture run validates workflow package
- **WHEN** a workflow skill includes a fixture
- **THEN** the fixture runner can execute the workflow using fixture provider fallback and verify expected public events or state

### Requirement: Skill activation is permission-aware and audited
Skill catalog activation, workflow selection, tool allowlist use, and skill-declared external actions SHALL be evaluated through the permission policy and persisted to redacted audit records.

#### Scenario: Imported skill invocation
- **WHEN** an imported or untrusted skill is selected for a run
- **THEN** the system SHALL ask or deny according to policy and SHALL expose frontend-safe reasons without loading raw provider secrets

### Requirement: Skill diagnostics appear in doctor and trace export
Doctor and trace export SHALL include skill manifest validity, source priority, shadowing, model hints, permission metadata, workflow validation status, and diagnostics without exposing skill-provided secrets.

#### Scenario: Invalid skill manifest
- **WHEN** a skill manifest is invalid
- **THEN** doctor SHALL report the invalid skill, severity, path/source metadata, and remediation hint while keeping the local web loop available

