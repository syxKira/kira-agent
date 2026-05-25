## ADDED Requirements

### Requirement: On-demand project document retrieval

When a default-agent run has a project root, Kira SHALL expose read-only project search/read tools so the model can retrieve local project documents only when the task needs project facts, business background, or citations.

#### Scenario: Model retrieves local project documentation when needed

- **WHEN** a run is created with a project root and no explicit `project_context_query`
- **THEN** Kira SHALL NOT pre-inject prompt-derived project snippets by default
- **THEN** Kira SHALL provide project search/read tool schemas to the model
- **THEN** tool results SHALL be fed back to the model as bounded tool messages

#### Scenario: Prompt-derived preloading is opt-in

- **WHEN** a run is created with `auto_project_context` set to true
- **THEN** Kira MAY search allowed project files using bounded lexical retrieval derived from the prompt
- **THEN** selected snippets SHALL be injected as untrusted project ContextItems with citations and retrieval trace metadata

### Requirement: Live retrieval handles mixed natural-language prompts

Kira SHALL derive bounded keyword searches from natural-language prompts so live project retrieval can match business terms embedded in longer Chinese or code-mixed requests.

#### Scenario: Embedded business term matches project docs

- **WHEN** a prompt contains a business identifier such as `adtracker` inside a longer request
- **THEN** live retrieval SHALL search that identifier in addition to the original prompt text
