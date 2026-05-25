## ADDED Requirements

### Requirement: cis-mira study is recorded as a Kira frontend contract

Kira SHALL maintain a frontend study directory that records which cis-mira chat
patterns Kira adopts, adapts, or rejects before implementing the Stage 13-15
chat rebuild.

#### Scenario: Study names concrete reference files

- **WHEN** a developer opens the Stage 12 study docs
- **THEN** the docs SHALL list concrete cis-mira source files for chat layout, message rendering, reasoning, tool activity, composer behavior, and streaming behavior

#### Scenario: Study separates product patterns from business dependencies

- **WHEN** a developer reads the study docs
- **THEN** the docs SHALL identify interaction patterns Kira should reuse
- **THEN** the docs SHALL identify cis-mira business dependencies that Kira should not blindly import

### Requirement: Frontend dependency policy permits useful isolated UX dependencies

Kira SHALL NOT import cis-mira's large frontend stack wholesale, but SHALL allow
small stable dependencies when they directly improve user experience and remain
isolated behind Kira-owned components.

#### Scenario: A small UX dependency is justified

- **WHEN** a future frontend change proposes a dependency for markdown, collapsible UI, tooltips, icons, virtual lists, or browser visual tests
- **THEN** the change SHALL explain the user-experience benefit and the isolation boundary
- **THEN** the dependency SHALL NOT require adopting cis-mira's business state model, service hooks, tracking, or multi-agent product model

