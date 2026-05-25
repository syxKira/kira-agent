## ADDED Requirements

### Requirement: Controlled shell tool

Kira SHALL expose a shell execution tool that runs bounded commands from a project-local working directory.

#### Scenario: Shell command runs inside project root

- **WHEN** the agent invokes `run_shell_command` with a project root and a relative or project-local cwd
- **THEN** Kira SHALL run the command with shell semantics from that cwd
- **THEN** Kira SHALL return exit code, bounded stdout, bounded stderr, duration, cwd metadata, and truncation flags

#### Scenario: Cwd outside project is rejected

- **WHEN** the requested cwd resolves outside the selected project root
- **THEN** Kira SHALL reject the command before execution
- **THEN** Kira SHALL return a structured `path_outside_root` style tool error

#### Scenario: Shell output is bounded and redacted

- **WHEN** command output exceeds configured limits or includes secret-like values
- **THEN** Kira SHALL cap the output before returning it to the model/frontend
- **THEN** Kira SHALL redact recognized secrets in returned output and metadata

#### Scenario: Shell command times out

- **WHEN** a command exceeds its timeout
- **THEN** Kira SHALL terminate the process and return a structured timeout error with bounded partial output

### Requirement: Shell tool is available to project-bound default agent runs

Kira SHALL expose `run_shell_command` to the default agent loop when a run is bound to a project root.

#### Scenario: Project run includes shell tool

- **WHEN** a non-fixture run is created with a project root
- **THEN** the default agent loop SHALL include the shell tool in its OpenAI-compatible tool list
- **THEN** tool events SHALL be streamed as `tool_start` and `tool_result`

#### Scenario: JSON synthesis shell calls are internally rejected

- **WHEN** a structured-data task causes the model to request a shell command only to synthesize, compact, timestamp, or print JSON
- **THEN** Kira SHALL reject that tool result internally before running the command
- **THEN** Kira SHALL guide the model to call the target script directly with the final minified JSON
- **THEN** the rejected synthesis command SHALL NOT appear as a user-visible `tool_start` / `tool_result` pair
