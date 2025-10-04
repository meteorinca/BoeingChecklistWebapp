# PRD: Boeing Checklist Webapp

## Overview
The Boeing Checklist Webapp is a lightweight browser tool for drafting, organizing, and printing aviation-style checklists. The refreshed MVP stores data in Firestore so the same checklist can be edited from any device with the shared password.

## Target Users
- Flight sim hobbyists who want custom flows for their home cockpit.
- Pilots-in-training who need a tidy way to rewrite instructor notes.
- Small safety teams that just need a printable checklist for one aircraft or scenario.

## Goals
1. Provide an intuitive editor for creating checklist sections and items in a familiar left/right layout.
2. Offer a distraction-free review mode that prints cleanly on standard paper.
3. Make it simple to save progress and resume work from any device using the hosted Firebase deployment.

## Success Criteria
- First-time users can create a two-section checklist with at least five items in under ten minutes.
- Printed checklists fit on one or two pages without manual formatting.
- Returning to the app (local or hosted) restores the last saved checklist automatically.

## Scope
### Must Have
- Create, rename, and delete checklist sections.
- Add, edit, reorder, and remove checklist items with left/right text fields.
- Auto-save progress to Firestore with optimistic UI feedback.
- Print preview that mirrors the editing layout.

### Nice To Have
- Duplicate an existing checklist when starting a variation.
- Toggle simple themes for light or dark printing needs.
- Import/export checklists via YAML or Markdown for backup.

## Out of Scope
- Multi-user accounts or per-user security (shared-password only for now).
- Advanced formatting (rich text, file attachments, images).
- Offline-first Progressive Web App features.
- Mobile-first redesign beyond ensuring basic usability on tablets.

## User Stories
| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| US1 | As a user, I want to create sections and items so I can mirror my checklist flow. | Must Have | Editor supports adding/reordering/removing sections and items inline. |
| US2 | As a user, I want the app to remember my checklist so I can continue later. | Must Have | Firestore saves the latest edit and rehydrates the editor on load. |
| US3 | As a user, I want a print-friendly view so I can carry the checklist. | Must Have | Print preview matches editor ordering and fits standard paper sizes without clipping. |
| US4 | As a user, I want to duplicate or import checklists to speed up variations. | Nice To Have | Dedicated actions create copies or load YAML/Markdown successfully. |

## Non-Functional Requirements
- **Performance**: Editor interactions respond within 100 ms on modern laptops.
- **Availability**: Hosted Firebase deployment responds over HTTPS with <500 ms median latency.
- **Compatibility**: Support recent versions of Chrome, Edge, and Firefox on desktop.
- **Accessibility**: Meet WCAG AA color contrast and keyboard navigation for the editor and print view.

## Open Questions
- Should shared password authentication evolve into per-user signin once multiple crews need their own checklists?
- Do we need basic item status tracking (e.g., checkmarks) in addition to text fields?
- Is Firestore cost acceptable under expected usage, or should we enforce retention limits?
