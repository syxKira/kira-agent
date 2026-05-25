## ADDED Requirements

### Requirement: Package-backed skill discovery

The system SHALL discover workflow-capable skills from validated local skill packages in addition to built-in registry definitions.

#### Scenario: Workflow package is discoverable
- **WHEN** a local skill package includes valid `SKILL.md` and `skill.yaml` workflow metadata
- **THEN** the skill registry exposes the package as workflow-capable with public workflow metadata

#### Scenario: Invalid workflow package is not invocable
- **WHEN** workflow package validation fails
- **THEN** the package appears in validation diagnostics but is not selectable for graph execution

### Requirement: Skill activation loads workflow context

The system SHALL load package workflow context, references, and permission metadata only after explicit activation, validated auto route, or workflow-owned context need.

#### Scenario: Explicit activation selects package skill
- **WHEN** a run request names a valid package-backed skill ID
- **THEN** run creation stores selected skill metadata and loads bounded skill ContextItems for graph execution

### Requirement: Auto routing is bounded and progressive

The system SHALL support auto routing against summary metadata without loading full skill bodies before a route is chosen.

#### Scenario: Auto route uses summary metadata
- **WHEN** auto routing evaluates candidate skills
- **THEN** it uses catalog summary fields such as description and when-to-use metadata without loading full docs

