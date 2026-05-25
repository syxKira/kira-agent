## ADDED Requirements

### Requirement: Python execution uses Stage 09 permission checks
Controlled Python execution SHALL evaluate script source, cwd, args, env, timeout, output cap, and risk markers through the permission policy before execution.

#### Scenario: Risky temp script
- **WHEN** a temp Python script or risky args/env request is submitted
- **THEN** execution SHALL be denied or require approval according to policy and SHALL record a redacted permission decision

### Requirement: Python execution is audited and diagnosable
Controlled Python execution SHALL write audit records and doctor diagnostics for interpreter availability, cwd boundary, timeout, output truncation, exit status, and redacted error summaries.

#### Scenario: Python timeout
- **WHEN** a Python run times out
- **THEN** audit and trace export SHALL include timeout status, capped output summary, cwd metadata, and no raw secret values
