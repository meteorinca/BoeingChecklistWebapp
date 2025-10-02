# PRD: Boeing Checklist Maker MVP

## Overview
Boeing Checklist Maker is a web application that enables aviation enthusiasts and training teams to adapt the Boeing 737-800 normal checklist format into personalized procedures. The MVP delivers a browser-based editing experience backed by a lightweight Flask API, persisting checklists, and supporting exports in YAML and print-ready PDF.

## Target Users and Personas
- Flight sim hobbyists tailoring flows for home cockpit setups.
- Student pilots documenting instructor-specific callouts.
- Maintenance and safety coordinators adapting Boeing layouts to internal procedures.

## Goals
1. Provide a no-code editor that preserves Boeing checklist styling while enabling custom content.
2. Allow users to manage multiple checklists and version them via import/export as YAML.
3. Deliver print-ready output that matches the Boeing card layout for binders or kneeboards.

## Success Metrics (MVP Exit Criteria)
- 3/3 pilot or instructor evaluators can recreate their current paper checklist within 30 minutes.
- 100 percent of created checklists can be exported to YAML and re-imported without data loss.
- Printed PDF output aligns within 5 mm of the supplied Boeing template measurements when printed on US Letter or A4.

## In Scope (Functional Requirements)
1. **Template seeding**: Load the supplied Boeing 737-800 checklist as the default starting point.
2. **Checklist CRUD**: Create, open, rename, duplicate, and delete checklists saved to the server.
3. **Section management**: Add, remove, reorder, and rename sections (e.g., "Before Start"), while preserving style cues (uppercase heading, blue bar).
4. **Item management**: Add, remove, reorder, and edit checklist rows with left/right text columns and optional blank input lines.
5. **Formatting controls**: Support bold, italics, and blank underscores within items to match the Boeing look; enforce consistent typography and spacing.
6. **Autosave**: Persist changes on every edit with undo/redo support for the current session.
7. **YAML import/export**: Download and upload checklist definitions using a documented schema.
8. **Print/PDF workflow**: Offer an in-browser preview that can be printed to paper or saved as PDF with layout fidelity.
9. **Change log**: Record and display last edited timestamp and author name supplied by the user.
10. **Single-password access**: Gate the editor behind a Basic Auth screen that validates a shared password stored as an environment secret.

## Out of Scope (MVP)
- Real-time multi-user collaboration.
- Account management or multi-user authentication beyond the shared password gate.
- Mobile-first optimization beyond ensuring layouts degrade gracefully on tablets.
- Native Boeing font licensing beyond system-safe substitutes.
- Non-Boeing aircraft templates (future library).

## User Stories (MVP)
| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| US1 | As a user, I want to open the Boeing base checklist and start editing immediately. | Must Have | Default checklist loads on first visit; edits autosave. |
| US2 | As a user, I want to add a new section to capture airline-specific flows. | Must Have | User can add, name, and drag the section to desired position. |
| US3 | As a user, I want to export the checklist to YAML to share with teammates. | Must Have | Export button downloads YAML matching schema and round-trips. |
| US4 | As a user, I want to re-import a YAML file to continue edits. | Must Have | Import replaces current checklist after confirmation and validates schema. |
| US5 | As a user, I want to print the checklist in Boeing-style columns. | Must Have | Print view renders two-column layout optimized for paper/PDF. |
| US6 | As a user, I want to maintain several checklist variants. | Must Have | Checklist list displays stored files with timestamps; user can open or delete. |
| US7 | As a user, I want to undo my last change. | Should Have | Undo command steps back within current session history. |

## Content and UX Requirements
- Match Boeing color palette (light blue section bars, black text) using web-safe colors.
- Preserve two-column grid layout with equal column heights per page.
- Support responsive scaling to maintain printable aspect ratio on 8.5x11 and A4.
- Provide inline validation and tooltips explaining required fields (section names, row text).
- Include onboarding tips describing YAML structure and printing instructions.

## Data and Persistence Requirements
- Store checklists, sections, and items in SQLite for MVP, with JSON column capturing serialized layout ordering.
- Enforce checklist title uniqueness; maintain slug identifiers for file exports.
- YAML schema must include metadata (title, revision, author, created_at, updated_at) and ordered arrays for sections and items.

## Non-Functional Requirements
- **Performance**: <200 ms server response for CRUD operations under normal usage.
- **Compatibility**: Support latest Chrome, Edge, and Firefox on desktop; Safari 16+ optional but tested.
- **Security**: Validate imported YAML to prevent code injection; limit file size to 2 MB; enforce HTTPS-only Basic Auth backed by an environment-managed password hash (Firebase Secrets).
- **Accessibility**: Achieve WCAG 2.1 AA for color contrast and keyboard navigation.
- **Reliability**: Daily automated backup of SQLite DB; server restarts without data loss.

## Launch Checklist
- QA sign-off with scripted test cases covering CRUD, import/export, and print preview.
- Document YAML schema and print instructions in onboarding modal and README.
- Provide deployment guide for Firebase Hosting + Cloud Run (Flask container) with managed TLS and secret-based password configuration.

## Open Questions and Risks
- Do we need user-level authentication before sharing beyond a single workstation?
- Will the business supply licensed fonts (e.g., Boeing typeface) or use substitutions?
- Is browser-based print fidelity sufficient, or is a server-side PDF renderer required?
- How will we migrate existing checklists if future versions introduce schema changes?
