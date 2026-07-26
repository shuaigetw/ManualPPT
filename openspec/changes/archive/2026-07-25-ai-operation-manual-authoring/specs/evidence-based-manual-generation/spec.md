## ADDED Requirements

### Requirement: Evidence-linked step explanations
The system SHALL derive operation purpose, application context, environmental factors, process factors, reasons, expected results, and cautions only from user statements, versioned source documents, and captured execution evidence.

#### Scenario: Explanation lacks evidence
- **WHEN** the system cannot support an explanation from an allowed source
- **THEN** it SHALL mark the explanation pending confirmation and SHALL NOT invent content

### Requirement: Source document management
The system SHALL ingest approved PDF, Word, PowerPoint, web help, and structured documents while recording title, version, effective date, and source location.

#### Scenario: Source documents conflict
- **WHEN** two applicable sources provide conflicting instructions
- **THEN** the system SHALL show the conflict and SHALL require a user decision before formal publication

### Requirement: Editable manual script
The system SHALL generate an editable manual script before PowerPoint creation, organized into standard flow, branch flows, exception handling, and a coverage appendix.

#### Scenario: User reviews a draft
- **WHEN** execution evidence has been assembled
- **THEN** the user SHALL be able to change ordering, approved wording, screenshot selection, and annotations without altering original evidence

### Requirement: Step-level traceability
The system SHALL link every manual step to its workflow version, operation events, screenshot timestamp, source references, execution result, and trace identifier.

#### Scenario: Reader inspects a manual step
- **WHEN** a reviewer opens traceability details
- **THEN** the system SHALL identify the exact evidence and sources used for that step

### Requirement: PowerPoint generation
The system SHALL generate an editable PowerPoint from an approved manual script and SHALL include operation, target, reason, expected result, caution, and annotated screenshot as applicable.

#### Scenario: Manual script is not approved
- **WHEN** a user requests formal PowerPoint generation from an unapproved script
- **THEN** the system SHALL generate only a visibly labeled draft

### Requirement: Formal publication gate
The system SHALL mark a manual formal only when selected paths have explicit results, required screenshots and explanations exist, dangerous actions have authorization records, sensitive-data checks pass, workflow diffs are resolved, and a user signs off.

#### Scenario: Publication criterion fails
- **WHEN** any formal publication criterion remains unsatisfied
- **THEN** the system SHALL block formal status and SHALL list the unresolved criteria

### Requirement: Differential regeneration
The system SHALL compare a rerun against the prior workflow, UI, screenshots, and results and SHALL regenerate only affected manual content after user approval.

#### Scenario: Application UI changes
- **WHEN** a rerun finds an added, removed, relocated, or behaviorally changed element
- **THEN** the system SHALL present the difference and SHALL preserve the prior manual version until approval
