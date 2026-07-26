## ADDED Requirements

### Requirement: Multi-dimensional audience profiles
The system SHALL support selected combinations of proficiency, organizational level, purpose, language, and role permissions.

#### Scenario: User selects audience combinations
- **WHEN** a user configures publication
- **THEN** the system SHALL show the exact manual variants and count before generating them

### Requirement: Required audience categories
The system SHALL support novice, experienced, management, audit, executive management, middle management, frontline management, and frontline employee variants.

#### Scenario: Executive version is generated
- **WHEN** executive management is selected
- **THEN** the manual SHALL emphasize purpose, governance, metrics, and risk while preserving links to the same verified workflow facts

#### Scenario: Novice version is generated
- **WHEN** novice is selected
- **THEN** the manual SHALL provide detailed sequential guidance and screenshots without changing the verified operation

### Requirement: Permission-safe content
The system SHALL apply the audience role's field and workflow permissions to text, screenshots, appendices, and traceability details.

#### Scenario: Audience lacks field permission
- **WHEN** source evidence contains a field the target audience cannot view
- **THEN** the system SHALL remove or mask the field in that variant and SHALL not leak it through notes or metadata

### Requirement: Fact-preserving localization and summarization
The system SHALL preserve verified operational facts when translating, shortening, or adapting a manual.

#### Scenario: Language version is generated
- **WHEN** a user selects another language
- **THEN** translated instructions SHALL retain the same step conditions, outcomes, risks, and evidence identity

### Requirement: Company presentation templates
The system SHALL support approved company PowerPoint templates for colors, fonts, logos, headers, footers, and confidentiality markings while keeping content separate from layout.

#### Scenario: Company template changes
- **WHEN** a user applies a new approved template to an existing manual
- **THEN** the system SHALL re-layout the manual without re-executing the browser workflow

### Requirement: Configurable retention
The system SHALL apply configurable retention periods independently to raw video, screenshots, workflow evidence, audits, and published manuals.

#### Scenario: Raw video retention expires
- **WHEN** an approved raw-video retention period expires
- **THEN** the system SHALL delete the raw video without deleting evidence or audit records that remain under their own policies
