# Task Plan: Boeing Checklist Maker MVP

## Product Foundations
- [ ] Confirm Boeing base checklist assets and typography references
- [ ] Resolve open questions on fonts, PDF fidelity, and future authentication needs

## Backend & Data Layer
- [ ] Set up Flask project structure with application factory and blueprints
- [ ] Implement SQLAlchemy models for checklists, sections, items with ordering metadata
- [ ] Configure SQLite for local dev and plan Cloud SQL connection string for production
- [ ] Implement Alembic migrations covering initial schema
- [ ] Build checklist CRUD services with validation and ordering logic
- [ ] Create YAML adapter (export/import) with Marshmallow schema enforcement
- [ ] Add Basic Auth middleware reading bcrypt hash from environment secret
- [ ] Implement autosave-friendly endpoints (bulk PUT + PATCH)
- [ ] Create print-ready HTML/PDF endpoint leveraging Jinja template
- [ ] Instrument logging and `/health` endpoint

## Frontend (HTML/CSS/JS)
- [ ] Scaffold SPA shell served via Firebase Hosting
- [ ] Implement state store with undo/redo stack and autosave debounce
- [ ] Build section management UI (add, rename, reorder via drag-and-drop)
- [ ] Build item editor with left/right columns, formatting controls, blanks support
- [ ] Implement Boeing-themed styling (colors, typography, two-column grid)
- [ ] Add checklist selector list with timestamps and duplication/delete actions
- [ ] Integrate YAML import/export modals with client-side validation
- [ ] Build print preview route matching Boeing layout, optimized for PDF export
- [ ] Add onboarding tooltips and inline validation messaging

## Security & Compliance
- [ ] Enforce HTTPS-only access via Firebase Hosting configuration
- [ ] Store shared password hash in Google Secret Manager and inject into Cloud Run
- [ ] Add CSRF protection and request rate limiting for auth-protected endpoints
- [ ] Validate and sanitize user input and uploaded YAML payloads

## Testing & QA
- [ ] Write pytest suites for services, API endpoints, YAML round-trip, and auth
- [ ] Add frontend unit tests (vitest/Jest) for store logic and utilities
- [ ] Create Playwright end-to-end scripts for CRUD, import/export, and print flows
- [ ] Establish PDF layout regression tests (visual diff or measurements)
- [ ] Prepare manual QA checklist aligned to MVP user stories

## Deployment & Ops
- [ ] Author Dockerfile and Cloud Build config for Flask service
- [ ] Configure Firebase Hosting rewrites proxying API requests to Cloud Run
- [ ] Set up GitHub Actions pipeline for lint, tests, and Firebase deploy
- [ ] Provision Cloud SQL instance (if needed) and nightly backup job
- [ ] Document deployment/runbook detailing secrets, scaling, and rollback steps

## Documentation & Enablement
- [ ] Publish YAML schema guide and printing instructions in-app and README
- [ ] Create user onboarding walkthrough or quickstart video/script
- [ ] Capture change log metadata display requirements in UX specs

