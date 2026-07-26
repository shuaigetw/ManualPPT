## ADDED Requirements

### Requirement: Application discovery interview
The system SHALL collect the application's purpose, users, environments, tasks, roles, terminology, risks, known exceptions, target audiences, and output languages before formal publication.

#### Scenario: Missing discovery answer
- **WHEN** a user leaves a discovery answer incomplete
- **THEN** the system SHALL mark it as pending confirmation and SHALL allow only read-only exploration until required publication information is complete

### Requirement: Approved feature inventory
The system SHALL create a feature inventory and reachable workflow tree for the selected website, modules, roles, and tasks before execution.

#### Scenario: User selects all
- **WHEN** a user selects all items in the approved inventory
- **THEN** the system SHALL schedule every reachable and authorized function, role, option, button path, and declared exception in that scope

### Requirement: Canonical branching workflow
The system SHALL represent scripts, AI discoveries, and recorded demonstrations as one versioned model of states, steps, conditions, branches, roles, expected outcomes, and exceptions.

#### Scenario: Dropdown contains several options
- **WHEN** discovery finds a dropdown with several enabled options
- **THEN** the workflow SHALL contain a test action for every option

#### Scenario: Multi-select contains several options
- **WHEN** discovery finds a multi-select control
- **THEN** the workflow SHALL cover every option at least once and SHALL add combinations selected by risk and interaction analysis

#### Scenario: Interface exposes several buttons
- **WHEN** a state exposes buttons with distinct semantics
- **THEN** the workflow SHALL model each button as a separate path

### Requirement: Synchronized flow and step views
The system SHALL provide synchronized flowchart and step-table views of the canonical workflow.

#### Scenario: User edits a step
- **WHEN** a user changes a condition, branch, or step in either view
- **THEN** the system SHALL update the other view without changing unrelated workflow content

### Requirement: Versioned manual corrections
The system SHALL store manual deviations as proposed additions, replacements, skips, or branches and SHALL preserve prior workflow versions.

#### Scenario: Manual takeover differs from script
- **WHEN** a user performs a different action during manual takeover
- **THEN** the system SHALL show a version diff and SHALL NOT merge the change until the user confirms it
