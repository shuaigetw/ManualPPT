# hybrid-browser-capture Specification

## Purpose
TBD - created by archiving change ai-operation-manual-authoring. Update Purpose after archive.
## Requirements
### Requirement: Interchangeable capture modes
The system SHALL support scripted automation, AI-guided automation, and manual browser demonstration within the same resumable session.

#### Scenario: Script switches to manual and back
- **WHEN** a user pauses a script, demonstrates additional actions manually, and resumes scripted mode
- **THEN** the system SHALL retain one ordered evidence timeline and SHALL create a workflow change proposal for the manual segment

### Requirement: Semantic UI event capture
The system SHALL capture meaningful UI interactions including click, double-click, right-click, hover, drag, reorder, slider movement, selection, scrolling, expand, collapse, file drag-and-drop, chart, and canvas interactions.

#### Scenario: Pointer moves without interaction
- **WHEN** the pointer moves without targeting or changing a UI element
- **THEN** the system SHALL NOT create a manual step for each raw coordinate

### Requirement: Significant-state screenshots
The system SHALL capture screenshots after meaningful actions, completed input states, page or dialog transitions, validation messages, and material before-and-after changes.

#### Scenario: Repeated low-value frames
- **WHEN** consecutive frames show no material state change
- **THEN** the system SHALL merge or discard them and SHALL retain the evidence timestamps

### Requirement: Visual operation annotation
The system SHALL annotate manual screenshots with a cursor, arrow, or bounding highlight identifying the target element.

#### Scenario: Screenshot represents a click
- **WHEN** a screenshot is selected for a click step
- **THEN** the exported image SHALL visibly identify the clicked element without obscuring essential content

### Requirement: Capture-time sensitive data protection
The system SHALL prevent passwords, MFA codes, identity numbers, salary, bank accounts, tokens, and configured company secrets from entering logs, recordings, screenshots, or manuals.

#### Scenario: Sensitive input is displayed
- **WHEN** a sensitive field or configured sensitive region appears during capture
- **THEN** the system SHALL mask it at capture time and SHALL record only that a protected interaction occurred

### Requirement: Local-first capture
The system SHALL perform raw browser event capture, recording, masking, and screenshot preparation on the local device or approved company infrastructure.

#### Scenario: Unapproved external upload
- **WHEN** a capture component attempts to upload raw session data to an unapproved third party
- **THEN** the system SHALL block the transfer and SHALL record a security event

