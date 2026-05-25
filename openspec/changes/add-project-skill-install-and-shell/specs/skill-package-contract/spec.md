## ADDED Requirements

### Requirement: Skill frontmatter includes invocation metadata

Kira SHALL parse skill invocation frontmatter including `disable-model-invocation`, `user-invocable`, and `model-invocable`.

#### Scenario: Invocation metadata appears in public skill metadata

- **WHEN** a valid skill declares invocation frontmatter
- **THEN** the skill catalog SHALL expose frontend-safe invocation metadata
- **THEN** auto-routing SHALL respect disabled model invocation

### Requirement: Activated skill docs are chunked

Kira SHALL split long activated `SKILL.md` bodies into bounded ContextItems.

#### Scenario: Long skill docs preserve late instructions

- **WHEN** a selected skill has a `SKILL.md` body longer than the per-item context budget
- **THEN** Kira SHALL emit multiple ordered `skill_doc` ContextItems
- **THEN** later sections such as script execution instructions SHALL remain eligible for provider context

#### Scenario: Prompt selects relevant skill sections

- **WHEN** a selected skill document contains multiple templates or platform variants
- **THEN** Kira SHALL prefer sections whose headings or text match the run prompt
- **THEN** unrelated templates and send commands SHOULD be omitted from the activated `skill_doc` ContextItems
