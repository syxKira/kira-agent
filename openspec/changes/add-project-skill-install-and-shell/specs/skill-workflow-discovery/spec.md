## ADDED Requirements

### Requirement: Prompt auto-routes to matching local skills

Kira SHALL be able to select an active local skill from catalog metadata when no explicit skill is selected.

#### Scenario: Prompt matches one skill

- **WHEN** the prompt clearly matches one active valid skill and the skill allows model invocation
- **THEN** run creation SHALL bind that skill to the run
- **THEN** Kira SHALL load the activated skill context before provider execution

#### Scenario: Explicit skill selection wins

- **WHEN** the run request names a skill id
- **THEN** Kira SHALL use the named skill instead of auto-routing

#### Scenario: Disabled model invocation is not auto-routed

- **WHEN** a matching skill declares `disable-model-invocation: true` or `model-invocable: false`
- **THEN** Kira SHALL NOT select it through auto-routing
