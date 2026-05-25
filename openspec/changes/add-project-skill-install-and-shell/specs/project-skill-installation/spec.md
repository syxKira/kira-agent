## ADDED Requirements

### Requirement: Project skill zip installation

Kira SHALL install local skill zip packages into the selected project root under `.kira/skills`.

#### Scenario: Valid zip installs a skill

- **WHEN** the user requests installation of a zip containing exactly one top-level skill directory with a valid `SKILL.md`
- **THEN** Kira SHALL extract the package to `.kira/skills/<skill-id>`
- **THEN** Kira SHALL return frontend-safe package metadata and diagnostics

#### Scenario: Unsafe zip paths are rejected

- **WHEN** a zip entry resolves outside the installation directory or uses an absolute path
- **THEN** Kira SHALL reject the install without writing that entry
- **THEN** Kira SHALL return a structured installation error

#### Scenario: Platform metadata is ignored

- **WHEN** a zip contains `__MACOSX`, AppleDouble `._*`, `__pycache__`, or `.pyc` entries
- **THEN** Kira SHALL skip those entries during installation
- **THEN** skipped metadata SHALL NOT appear as separate invalid skills

### Requirement: Install requests are audited

Kira SHALL persist redacted audit records for skill installation attempts.

#### Scenario: Install audit record is written

- **WHEN** a skill install succeeds or fails
- **THEN** Kira SHALL record the action, project root, zip basename, status, diagnostics, and installed skill id when available
- **THEN** Kira SHALL NOT persist raw secret-like file contents in the audit record
