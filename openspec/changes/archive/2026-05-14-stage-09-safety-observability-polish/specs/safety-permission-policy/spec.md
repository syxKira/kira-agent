## ADDED Requirements

### Requirement: Local actions use a structured permission decision
The system SHALL evaluate safety-sensitive local actions through a structured permission decision containing action, subject metadata, decision, reasons, redacted inputs, and audit correlation metadata.

#### Scenario: Allowed action returns metadata
- **WHEN** a read-only project file action is inside the selected project root and not ignored or sensitive
- **THEN** the permission result SHALL be `allow` with redacted project/root/path metadata and a reason explaining the allow decision

#### Scenario: Risky action asks or denies
- **WHEN** a temp Python script, unknown provider override, imported skill action, project/user memory write, transcript delete, or replacement inspection is requested
- **THEN** the permission result SHALL be `ask` or `deny` with frontend-safe reasons and no raw secrets

### Requirement: Permission defaults cover all Stage 01-08 safety boundaries
The system SHALL define default permission behavior for provider readiness, provider/model override, project file read/search, controlled Python execution, skill invocation, skill tool/action use, workflow external action, memory writes/lifecycle, transcript archive/delete/compact/fork/rollback, and retained replacement inspection.

#### Scenario: Default policy is deterministic
- **WHEN** tests evaluate the default policy without user-local configuration
- **THEN** decisions SHALL be deterministic and SHALL NOT require a real provider key, external service, or project mutation

### Requirement: Permission decisions are redacted before persistence or response
The system SHALL redact API keys, bearer tokens, cookies, private keys, `.env` content, provider config secrets, hidden thinking, and high-risk personal/customer data from permission responses and persisted records.

#### Scenario: Secret in action args
- **WHEN** permission input includes `sk-secret` or an `api_key` field
- **THEN** the API response, audit hint, trace export, and frontend display SHALL omit or redact the raw secret
