# Task Plan (Working): Boeing Checklist Webapp

_Updated for the Firestore + Firebase deployment effort. Check items off as you land them._

## Foundations
- [ ] Confirm Firestore project, service account, and Firebase Hosting targets.
- [ ] Document shared password rotation and credential management.

## Backend
- [x] Replace SQLAlchemy + SQLite with Firestore document storage.
- [x] Ensure autosave writes updates atomically and returns helpful errors.
- [x] Keep duplicate/import/export flows working with the new persistence layer.
- [ ] Add unit or smoke tests for Firestore integration (emulator or stubbed client).

## Frontend
- [ ] Review API payload changes and keep editor state in sync with new fields (e.g., `theme`).
- [ ] Validate autosave + undo/redo flows against hosted backend.
- [ ] Provide natural theming toggle (default + high-contrast).

## Deployment
- [x] Add Dockerfile for Cloud Run.
- [x] Add firebase.json rewrites to route `/api` to Cloud Run.
- [ ] Create CI/deploy script or GitHub Action for container builds (optional).
- [ ] Configure Firestore indexes and security rules for production.

## QA
- [ ] Smoke test create/edit/duplicate/import/print scenarios in Chrome, Edge, and Firefox.
- [ ] Verify keyboard navigation and focus order through the editor controls.
- [ ] Load the hosted build over HTTPS and confirm caching headers/static assets.

## Documentation
- [x] Update README usage notes and deployment instructions.
- [x] Refresh architecture docs for Firestore + Firebase.
- [ ] Record a short checklist for manual regression before each release.
