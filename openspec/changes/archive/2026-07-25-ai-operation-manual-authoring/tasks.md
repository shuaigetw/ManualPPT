## 1. Project Foundations

- [x] 1.1 Select and document the ManualPPT desktop, extension, service, persistence, and PowerPoint technology stack
- [x] 1.2 Define the feature flag, localhost/staging origin allowlist, fixture-account policy, and retention defaults
- [x] 1.3 Install approved dependencies using the package managers selected for ManualPPT
- [x] 1.4 Define trace identifiers, idempotency keys, event sequence rules, and append-only audit event types

## 2. Canonical Workflow Domain

- [x] 2.1 Implement typed domain entities for projects, scopes, audiences, role sessions, workflow versions, states, steps, transitions, branches, risks, executions, checkpoints, evidence, approvals, sources, drafts, and publications
- [x] 2.2 Implement workflow validation for reachable paths, dropdown options, multi-select coverage, independent buttons, roles, and exception outcomes
- [x] 2.3 Implement synchronized flowchart and step-table domain commands
- [x] 2.4 Implement immutable workflow version diffs for add, replace, skip, and branch corrections
- [x] 2.5 Add governance checks to every workflow and execution write path
- [x] 2.6 Add persistence migrations, repository adapters, and durable Agent checkpoints

## 3. Discovery and Source Ingestion

- [x] 3.1 Implement the discovery interview and pending-confirmation state
- [x] 3.2 Implement read-only feature inventory and reachable workflow-tree generation
- [x] 3.3 Implement PDF, Word, PowerPoint, web-help, and structured-document ingestion through the integration boundary
- [x] 3.4 Implement source versioning, effective dates, citations, and conflict detection
- [x] 3.5 Implement Agent orchestration for discovery, planning, evidence analysis, and drafting

## 4. Local Browser and Desktop Capture

- [x] 4.1 Build the Chrome/Edge extension shell and enterprise-configurable origin allowlist
- [x] 4.2 Capture semantic DOM targets, accessibility roles, stable identifiers, candidate locators, and reference images
- [x] 4.3 Capture meaningful pointer, selection, scrolling, drag-and-drop, chart, and canvas interactions
- [x] 4.4 Implement significant-state screenshot selection and target annotations
- [x] 4.5 Build the local desktop session controller for recording, manual takeover, and offline event buffering
- [x] 4.6 Implement capture-time masking and block unapproved raw-session uploads
- [x] 4.7 Implement ordered evidence ingestion with hashes, acknowledgements, and duplicate protection

## 5. Governed Automation Execution

- [x] 5.1 Implement approved-scope execution planning and honest coverage statuses
- [x] 5.2 Implement per-action permission, scope, skill, and risk classification checks
- [x] 5.3 Implement dangerous-action warnings and one-time second-confirmation grants
- [x] 5.4 Implement human login/MFA handoff without credential capture
- [x] 5.5 Implement semantic element resolution and ambiguous-match suspension
- [x] 5.6 Implement checkpoints, pause, resume, termination, kill switch, and isolated branch retry
- [x] 5.7 Implement synthetic test-data proposals and user-confirmed cleanup plans

## 6. Manual Drafting and PowerPoint

- [x] 6.1 Implement evidence-bound explanations for purpose, application, environment, process, reason, outcome, and caution
- [x] 6.2 Implement pending-confirmation behavior for unsupported statements and unresolved source conflicts
- [x] 6.3 Build the editable manual script with standard flow, branches, exceptions, and coverage appendix
- [x] 6.4 Implement step-level traceability from draft content to source, event, screenshot, result, workflow version, and trace identifier
- [x] 6.5 Implement editable PowerPoint generation with annotated screenshots
- [x] 6.6 Implement company template ingestion and content-layout separation
- [x] 6.7 Implement the formal publication gate and visibly labeled incomplete/draft output

## 7. Audience Variants and Lifecycle

- [x] 7.1 Implement audience profiles across proficiency, management level, purpose, language, role, and permissions
- [x] 7.2 Implement novice, experienced, management, audit, executive, middle-management, frontline-management, and frontline-employee renderers
- [x] 7.3 Enforce field-level and workflow-level masking in text, images, notes, metadata, and appendices
- [x] 7.4 Implement fact-preserving localization and summarization checks
- [x] 7.5 Implement variant selection, generation-count preview, and reusable company presets
- [x] 7.6 Implement application-rerun diffs and selective manual regeneration
- [x] 7.7 Implement independent retention and deletion jobs for raw video, screenshots, evidence, audits, and publications

## 8. Deterministic Verification

- [x] 8.1 Add pytest domain tests for workflow coverage, version diffs, source conflicts, checkpoints, retention, and publication gates
- [x] 8.2 Add pytest governance tests proving unauthorized, unsafe-origin, sensitive-data, and dangerous-action paths are blocked
- [x] 8.3 Add integration tests for extension-to-desktop-to-backend event ordering, masking, evidence integrity, and trace identifiers
- [x] 8.4 Add deterministic Playwright tests using `data-testid` for script/manual switching, scope approval, dangerous confirmations, interruption choices, review, and publication
- [x] 8.5 Add role-based Playwright tests proving unauthorized fields and screenshots never appear in generated variants
- [x] 8.6 Run the selected local Agent exploration tool against localhost or staging with fixture accounts to discover multi-role edge cases
- [x] 8.7 Convert each confirmed exploratory finding into a deterministic Playwright regression
- [x] 8.8 Run all tests with the selected ManualPPT test runners and save machine-readable results
- [x] 8.9 Verify generated PowerPoint files visually and structurally across required audience and language samples
