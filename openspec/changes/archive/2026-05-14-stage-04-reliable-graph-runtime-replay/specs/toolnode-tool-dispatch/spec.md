## MODIFIED Requirements

### Requirement: Tool result normalization

The system SHALL normalize ToolNode results into graph state, Kira event payloads, persisted event records, and side-effect ledger records without exposing internal tool objects or unbounded raw output.

#### Scenario: Tool result becomes Kira event payload

- **WHEN** a workflow tool call succeeds
- **THEN** the event stream includes a structured payload with tool name, status, bounded result data, and idempotency metadata when applicable

#### Scenario: Tool error becomes structured graph error

- **WHEN** a workflow tool call returns a validation or execution error
- **THEN** the graph run emits and persists a structured error or tool-result payload that preserves the Stage 02 error code and message

## ADDED Requirements

### Requirement: Tool calls receive idempotency metadata

The system SHALL attach stable idempotency metadata to graph tool calls before execution.

#### Scenario: Tool call has idempotency key

- **WHEN** a graph workflow invokes a Stage 02 tool through ToolNode
- **THEN** the runtime computes and records an idempotency key for that call

#### Scenario: Completed tool call can be reused

- **WHEN** a resumed graph reaches a completed ledger entry for the same tool call
- **THEN** the runtime reuses the stored result rather than invoking the tool again
