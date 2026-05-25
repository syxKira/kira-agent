## MODIFIED Requirements

### Requirement: Inspector surfaces follow the Stage 10 dark shell

The frontend SHALL keep skill, project knowledge, memory, diagnostics, audit, trace, permission, and replacement inspection surfaces functionally equivalent to Stage 10 when they are reachable, but SHALL NOT render them in the default chat surface; the default workbench SHALL remain a chat-first layout (rail + sticky header + scrollable timeline + sticky composer) without an always-visible operator inspector, prominent inspector entry point, or fixture run buttons.

#### Scenario: Default workbench omits operator inspector

- **WHEN** the workbench loads in its default state at desktop or narrow viewport widths
- **THEN** the frontend SHALL NOT render the `Conversations` (with select/Create/Refresh/Compact controls), `Skills`, `Memory`, `Project`, `Context`, or `Safety` operator panels in the default chat surface
- **THEN** the frontend SHALL NOT render a prominent `Inspector` entry point or the `Run fixture`, `Run error fixture`, or `Run HITL fixture` buttons in the default chat surface

#### Scenario: Inspector panels remain functionally equivalent when reachable

- **WHEN** the user reaches a skill, project knowledge, memory, diagnostics, audit, trace, permission, or replacement inspection surface through an explicit non-default developer/debug affordance, debug route, environment-gated toggle, or future inspector design
- **THEN** the frontend SHALL show the same existing frontend-safe data and actions in the Stage 10 visual shell
- **THEN** the UI SHALL preserve existing redaction, permission, no-secret, hidden-thinking, and bounded-output behavior

#### Scenario: Narrow viewport uses drawer behavior when inspector is reachable

- **WHEN** inspector surfaces are reached through an explicit affordance at a narrow viewport width
- **THEN** the frontend SHALL move those surfaces behind drawer, tab, or sheet controls
- **THEN** the main timeline and composer SHALL remain the primary visible workflow
