# governed-automation-execution Specification

## Purpose
TBD - created by archiving change ai-operation-manual-authoring. Update Purpose after archive.
## Requirements
### Requirement: Allowlisted test environments
The system SHALL execute browser automation only against approved localhost or staging origins using fixture accounts and synthetic or approved test data.

#### Scenario: Production origin requested
- **WHEN** an execution target is not an approved localhost or staging origin
- **THEN** the system SHALL refuse to start and SHALL identify the rejected origin

### Requirement: Read-only exploration boundary
The system SHALL keep discovery read-only until a user approves the workflow scope and any required test-data plan.

#### Scenario: Discovery encounters a write action
- **WHEN** discovery reaches an action that can create, modify, submit, approve, pay, or delete
- **THEN** the system SHALL record the candidate path without executing the action

### Requirement: Per-action governance
The system SHALL authorize each side-effecting action using the intersection of the originating user's permissions, the approved workflow scope, and the Agent skill authorization.

#### Scenario: Permission intersection denies action
- **WHEN** any required authorization source denies an action
- **THEN** the system SHALL block the action and SHALL record the denial with a trace identifier

### Requirement: Repeated confirmation for dangerous actions
The system SHALL require a separate second confirmation for every dangerous action and SHALL display the action, affected test data, consequences, recovery method, and one-time authorization scope.

#### Scenario: User confirms one dangerous action
- **WHEN** a user confirms a dangerous action
- **THEN** the system SHALL authorize only that action and SHALL request confirmation again for the next dangerous action

#### Scenario: User declines dangerous action
- **WHEN** a user declines the confirmation
- **THEN** the system SHALL not execute the action and SHALL mark the path as declined rather than passed

### Requirement: Human authentication handoff
The system SHALL pause for manual login or an approved credential mechanism and SHALL never read or persist passwords, MFA codes, or session secrets.

#### Scenario: MFA is required
- **WHEN** the target application requests MFA
- **THEN** the system SHALL hand control to the user and SHALL resume only after authentication succeeds without capturing the verification secret

### Requirement: Resumable execution
The system SHALL checkpoint safe workflow states and SHALL permit pause, resume, branch retry, or termination.

#### Scenario: Execution is interrupted
- **WHEN** a run cannot continue
- **THEN** the system SHALL explain the cause, completed coverage, and remaining work and SHALL offer pause-for-resume or terminate options

#### Scenario: User terminates a partial run
- **WHEN** a user terminates an incomplete run
- **THEN** the system SHALL retain completed evidence by default and SHALL label any resulting draft and coverage report as incomplete

### Requirement: Honest coverage reporting
The system SHALL distinguish passed, failed, blocked, declined, not reached, and not selected paths and SHALL never report unexecuted paths as successful.

#### Scenario: Unsafe path cannot be restored
- **WHEN** a path cannot be safely executed or recovered in the test environment
- **THEN** the system SHALL mark it blocked with a reason and human verification instructions

### Requirement: Append-only execution audit
The system SHALL append immutable audit events for scope approval, authorization, dangerous confirmations, execution outcomes, pauses, resumes, terminations, and evidence changes.

#### Scenario: Audit event already exists
- **WHEN** an existing audit event would otherwise be changed or removed
- **THEN** the system SHALL append a correcting event instead of updating or deleting the original

