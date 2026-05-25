## ADDED Requirements

### Requirement: Frontend visual smoke covers the Mira-like chat surface

Kira SHALL provide local browser-level smoke coverage for the default Mira-like
chat UI using deterministic fixtures that do not require a real provider key.

#### Scenario: Required chat states are captured

- **WHEN** the visual smoke suite runs
- **THEN** it SHALL cover welcome, normal chat, streaming/status, reasoning, tool activity, HITL, error, and long transcript states
- **THEN** it SHALL include desktop and narrow viewport coverage

### Requirement: Visual smoke blocks known bad chat regressions

The visual smoke suite SHALL fail when the UI regresses to known bad patterns
from the pre-rebuild workbench.

#### Scenario: Event-dashboard regressions fail

- **WHEN** the default chat surface shows a prominent `Completed` card, default inspector panels, fixture/debug controls, or event-count dashboard content as primary UI
- **THEN** the visual smoke suite SHALL fail

#### Scenario: Conversation regressions fail

- **WHEN** one assistant answer is scattered across multiple assistant blocks, thinking is expanded by default, tool output appears as answer text, or submitted prompt text remains in the composer
- **THEN** the visual smoke suite SHALL fail

#### Scenario: Layout regressions fail

- **WHEN** desktop or narrow viewport screenshots show overlapping text, unreachable composer controls, or horizontal overflow in normal chat states
- **THEN** the visual smoke suite SHALL fail

