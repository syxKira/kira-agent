## ADDED Requirements

### Requirement: Safety and observability APIs are available
The API SHALL expose frontend-safe endpoints for doctor diagnostics, permission decisions or decision previews, audit export, trace export, and replacement inspection where allowed by policy.

#### Scenario: Doctor endpoint
- **WHEN** the frontend calls the doctor endpoint
- **THEN** the API SHALL return component statuses and remediation hints without raw secrets

#### Scenario: Audit endpoint
- **WHEN** the frontend requests audit records with filters
- **THEN** the API SHALL return bounded redacted records and pagination metadata

### Requirement: Safety errors are structured
The API SHALL return structured errors for denied permission, approval required, unsafe provider override, unsafe Python execution, unsafe memory write, unsafe transcript delete, inactive branch resume, and replacement inspection denial.

#### Scenario: Permission denied
- **WHEN** a policy decision denies an action
- **THEN** the response SHALL include a stable code, message, reasons, redacted subject metadata, and no raw secret values

### Requirement: Trace and audit exports are read-only
Doctor, audit, and trace export endpoints SHALL NOT trigger providers, execute tools, refresh retrieval, mutate memory, mutate transcripts, acquire run locks, or advance event streams.

#### Scenario: Export replay facts
- **WHEN** a run trace export is requested
- **THEN** the API SHALL return saved durable facts and SHALL NOT append new run events
