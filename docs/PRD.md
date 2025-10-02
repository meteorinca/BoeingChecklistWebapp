# PRD: Boeing Checklist Webapp

## Overview
The Boeing Checklist Webapp is a lightweight browser tool for drafting, organizing, and printing aviation-style checklists. The MVP focuses on helping a single operator capture procedures quickly without juggling spreadsheets or word processors.

## Target Users
- Flight sim hobbyists who want custom flows for their home cockpit.
- Pilots-in-training who need a tidy way to rewrite instructor notes.
- Small safety teams that just need a printable checklist for one aircraft or scenario.

## Goals
1. Provide an intuitive editor for creating checklist sections and items in a familiar left/right layout.
2. Offer a distraction-free review mode that prints cleanly on standard paper.
3. Make it simple to save progress and resume work on the same device.

## Success Criteria
- First-time users can create a two-section checklist with at least five items in under ten minutes.
- Printed checklists fit on one or two pages without manual formatting.
- Returning to the app restores the last saved checklist without extra setup.

## Scope
### Must Have
- Create, rename, and delete checklist sections.
- Add, edit, reorder, and remove checklist items with left/right text fields.
- Auto-save progress to the local database.
- Print preview that mirrors the editing layout.

### Nice To Have
- Duplicate an existing checklist when starting a variation.
- Toggle simple themes for light or dark printing needs.

## Out of Scope
- Multi-user accounts or collaboration.
- Advanced formatting (rich text, file attachments, images).
- YAML export/import, PDF rendering services, or external integrations.
- Mobile-first redesign beyond ensuring basic usability on tablets.

## User Stories
| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| US1 | As a user, I want to create sections and items so I can mirror my checklist flow. | Must Have | Editor supports adding/reordering/removing sections and items inline. |
| US2 | As a user, I want the app to remember my checklist so I can continue later. | Must Have | Refreshing or reopening the app restores the previous checklist automatically. |
| US3 | As a user, I want a print-friendly view so I can carry the checklist. | Must Have | Print preview matches editor ordering and fits standard paper sizes without clipping. |
| US4 | As a user, I want to duplicate a checklist when starting a variation. | Nice To Have | Duplicate action creates a copy with a new title ready for editing. |

## Non-Functional Requirements
- **Performance**: Editor interactions respond within 100 ms on modern laptops.
- **Compatibility**: Support recent versions of Chrome, Edge, and Firefox on desktop.
- **Accessibility**: Meet WCAG AA color contrast and keyboard navigation for the editor and print view.

## Open Questions
- Should checklists sync across browsers or remain device-specific for the MVP?
- Do we need basic item status tracking (e.g., checkmarks) in addition to text fields?