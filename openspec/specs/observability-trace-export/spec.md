# observability-trace-export Specification

## Purpose
TBD - created by archiving change stage-09-safety-observability-polish. Update Purpose after archive.
## Requirements
### Requirement: Trace export aggregates durable runtime facts
The system SHALL expose redacted trace exports that aggregate run context, provider attempts, Kira events, retries, side-effect ledger entries, checkpoints, project retrieval citations, memory citations, transcript context, compaction summaries, tool replacements, and branch decisions.

#### Scenario: Export run trace
- **WHEN** a trace export is requested for a `thread_id`
- **THEN** the response SHALL include the saved run view, provider selection metadata, context inclusion/omission decisions, event sequence metadata, and linked audit IDs without rerunning work

### Requirement: Trace export is bounded and read-only
The system SHALL apply limits, cursors, and summary-only defaults to large exports and SHALL NOT acquire run locks, trigger providers, run tools, refresh indexes, mutate memory, or change active conversation heads.

#### Scenario: Large trace export
- **WHEN** a run has many events, context items, retrieval results, or transcript parts
- **THEN** export SHALL return bounded results with truncation metadata and stable references to omitted records

### Requirement: Trace export redacts secrets and hidden thinking
Trace export SHALL redact provider secrets, env secrets, private keys, raw sensitive tool output, hidden thinking, and high-risk personal/customer data before persistence or response.

#### Scenario: Hidden thinking exists in events
- **WHEN** an event stream contains `thinking_delta`
- **THEN** trace export SHALL NOT merge that text into assistant answer text or future provider conversation history

