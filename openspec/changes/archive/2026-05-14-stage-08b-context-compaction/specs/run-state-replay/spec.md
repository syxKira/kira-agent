## ADDED Requirements

### Requirement: Run state includes compaction and replacement summaries
The run state projection endpoint SHALL include frontend-safe compaction summary and tool-output replacement references when a run used them for transcript context.

#### Scenario: State shows summary linkage
- **WHEN** a client requests state for a run that used a compaction summary
- **THEN** the state response includes summary ID, conversation ID, source range, stale status at run time, and budget metadata
- **THEN** the response excludes raw provider secrets and hidden thinking

#### Scenario: State shows replacement linkage
- **WHEN** a client requests state for a run that used a replacement stub
- **THEN** the state response includes replacement ID, source part ID, reason, omitted count, hash or hash prefix, and bounded summary metadata
- **THEN** raw replaced output is not exposed

### Requirement: Replay is read-only for compaction and replacement
The replay/debug export SHALL include saved compaction and replacement metadata without regenerating summaries, resolving raw replacement blobs, mutating transcript state, or creating memory records.

#### Scenario: Replay does not regenerate compaction
- **WHEN** replay/debug export is requested for a run that used compaction
- **THEN** replay reads saved summary metadata
- **THEN** replay does not call providers, create summaries, append transcript parts, or update stale status

#### Scenario: Replay does not resolve replacement blob
- **WHEN** replay/debug export is requested for a run with replacement records
- **THEN** replay returns saved frontend-safe replacement summary metadata
- **THEN** replay does not read raw replacement blobs, call tools, or expose raw replaced output

### Requirement: Replay records stale state as observed by the run
The replay/debug export SHALL report whether a compaction summary or replacement record was included, omitted, truncated, or stale at the time of the run context build.

#### Scenario: Replay preserves historical context decision
- **WHEN** a summary becomes stale after a completed run
- **THEN** replay for the completed run still shows the saved context decision from that run
- **THEN** replay does not rebuild context using the current summary status
