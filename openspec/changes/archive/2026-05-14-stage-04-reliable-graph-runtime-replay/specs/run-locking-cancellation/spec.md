## ADDED Requirements

### Requirement: Per-thread run lock

The system SHALL enforce one active graph executor per `thread_id` using a persistent run lock with owner, heartbeat, expiry, and status metadata.

#### Scenario: First executor acquires lock
- **WHEN** a graph run or resume starts for an unlocked `thread_id`
- **THEN** the executor acquires the run lock before executing graph work

#### Scenario: Duplicate executor is rejected
- **WHEN** a second executor attempts to run the same active `thread_id`
- **THEN** the backend returns current state or a structured conflict and does not start duplicate graph execution

### Requirement: Lock heartbeat and stale takeover

The system SHALL update lock heartbeats during active execution and SHALL only allow stale-lock takeover after expiry and takeover metadata are recorded.

#### Scenario: Heartbeat keeps lock active
- **WHEN** an executor is running normally
- **THEN** lock heartbeat is refreshed before expiry

#### Scenario: Stale lock is taken over
- **WHEN** a lock heartbeat is expired
- **THEN** a new executor may take over after recording stale-lock metadata

### Requirement: Stop and cancellation

The system SHALL support stop/cancel behavior that marks a run as cancelling, stops scheduling new graph work, checkpoints a terminal cancelled projection when possible, and keeps the run inspectable.

#### Scenario: Stop marks cancelling
- **WHEN** a user or shutdown path requests stop for an active run
- **THEN** the run state shows cancelling or cancelled status and no new graph nodes are scheduled

#### Scenario: Cancelled run remains inspectable
- **WHEN** a run is cancelled
- **THEN** state and replay endpoints remain available for that `thread_id`

### Requirement: Graceful shutdown handling

The system SHALL attempt to drain active graph runs to a safe checkpoint boundary during graceful shutdown.

#### Scenario: Shutdown checkpoints active run
- **WHEN** shutdown begins while a graph run is active
- **THEN** the runtime attempts to checkpoint state and marks the projection with shutdown/cancellation metadata

#### Scenario: Shutdown avoids new work
- **WHEN** shutdown is in progress
- **THEN** no new graph execution is started for active or queued runs

### Requirement: Resume conflict protection

The system SHALL protect resume operations from duplicate active executors and stale state.

#### Scenario: Duplicate resume conflict
- **WHEN** two resume requests arrive for the same `thread_id`
- **THEN** only one request can acquire the lock and continue execution

#### Scenario: Resume after terminal run is structured
- **WHEN** resume is requested for a completed or non-resumable cancelled run
- **THEN** the backend returns a structured terminal-state error
