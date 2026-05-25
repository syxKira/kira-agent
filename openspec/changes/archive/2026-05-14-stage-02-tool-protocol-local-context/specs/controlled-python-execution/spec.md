## ADDED Requirements

### Requirement: Execute Python scripts under control

The system SHALL provide `run_python_script` as a controlled Python subprocess tool, not a general shell.

#### Scenario: Python script runs with structured result

- **WHEN** the tool runs an allowed project-relative Python script
- **THEN** it returns exit code, stdout, stderr, duration metadata, cwd metadata, truncation flags, and `ok` status in the `ToolResult` envelope

### Requirement: Enforce cwd and script boundaries

The system SHALL validate script paths and cwd values against allowed project roots before execution.

#### Scenario: Script outside root is rejected

- **WHEN** the requested script path resolves outside the allowed project root
- **THEN** the tool returns a structured permission error and does not start a subprocess

#### Scenario: Cwd outside root is rejected

- **WHEN** the requested cwd resolves outside the allowed project root
- **THEN** the tool returns a structured permission error and does not start a subprocess

### Requirement: Avoid shell semantics

The system SHALL execute Python using an argv list without shell expansion, command separators, pipes, redirects, or arbitrary shell commands.

#### Scenario: Shell-like input is not interpreted

- **WHEN** a request includes shell control syntax as part of the script path or arguments
- **THEN** the tool treats it as invalid input or literal argv data and does not execute a shell command

### Requirement: Enforce timeout and output caps

The system SHALL enforce timeout, stdout cap, and stderr cap controls for Python execution.

#### Scenario: Timeout returns structured error

- **WHEN** a Python script exceeds the configured timeout
- **THEN** the subprocess is terminated and the tool returns a timeout `ToolResult` with duration metadata

#### Scenario: Output is truncated

- **WHEN** stdout or stderr exceeds the configured output cap
- **THEN** the tool returns capped output and metadata indicating which streams were truncated

### Requirement: Filter environment variables

The system SHALL pass only allowlisted environment variables to Python subprocesses.

#### Scenario: Non-allowlisted environment is omitted

- **WHEN** the parent process contains environment variables outside the configured allowlist
- **THEN** the Python subprocess does not receive those variables unless explicitly allowed
