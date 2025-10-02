# Master Design: Boeing Checklist Maker MVP

## Architecture Overview
Boeing Checklist Maker follows a client-server model. Static assets live on Firebase Hosting, while a containerized Flask backend runs on Google Cloud Run behind Firebase Hosting rewrites. The frontend delivers a single-page editing experience, and the backend exposes REST APIs for checklist data, YAML import/export, and PDF rendering. Persistence uses SQLite for local development with the option to swap to Cloud SQL (PostgreSQL) in production via SQLAlchemy.

```
+------------+        +-----------------+        +-------------+
|  Browser   | <----> | Firebase Hosting| <----> |  Cloud Run   |
+------------+        +--------+--------+        +------+------+
                              |                      |
                              v                      v
                        Static SPA assets     SQLAlchemy ORM
                                                (Cloud SQL /
                                                   SQLite)
```

## Technology Stack
- Python 3.11+, Flask 3.x, SQLAlchemy ORM, Marshmallow for schema validation.
- PyYAML for YAML serialization/deserialization with safe loaders.
- WeasyPrint or browser print CSS for PDF output (final choice pending fidelity validation).
- Vanilla JavaScript ES modules bundled with Vite (build-time only) or native import maps; no third-party JS frameworks in runtime.
- HTML/CSS with CSS Grid for Boeing-style two-column layout; print stylesheet controls paper output.
- Firebase Hosting for static delivery, Cloud Run for the Flask API, Artifact Registry + Cloud Build for container packaging, Firebase CLI for deploy orchestration.

## Backend Components
- **Application factory**: configures Flask app, database session, blueprints, and error handlers.
- **Checklist service**: encapsulates CRUD logic, ordering of sections/items, and change tracking metadata.
- **YAML adapter**: validates YAML payloads against schema, converts to/from ORM models, and safeguards against arbitrary object loading.
- **PDF service**: prepares print-ready HTML using Jinja templates. Primary path uses `window.print()` with print stylesheet; fallback server route generates PDF via WeasyPrint when a binary is required.
- **Auth middleware**: single-password Basic Auth verifier comparing the incoming credentials to a bcrypt hash stored in environment secret `APP_SHARED_PASSWORD_HASH`.
- **Error handling middleware**: returns JSON error envelopes with codes for validation, not found, and server errors.

## Data Model (SQLite / Cloud SQL)
- `checklists`: id (uuid), title, slug, author, notes, created_at, updated_at.
- `sections`: id (uuid), checklist_id (fk), title, position, notes.
- `items`: id (uuid), section_id (fk), left_text, right_text, formatting_flags (json), position.
- `attachments` (optional future): pdf, assets (not in MVP but reserved).
- Schema migrations via Alembic to ease future upgrades and map from SQLite (dev) to Cloud SQL PostgreSQL (prod).

## API Surface (JSON)
- `GET /api/checklists`: list metadata (id, title, updated_at, author).
- `POST /api/checklists`: create from template or blank; body accepts title and author.
- `GET /api/checklists/<id>`: fetch full checklist payload (sections, items ordered).
- `PUT /api/checklists/<id>`: replace checklist data; body uses same structure as GET.
- `PATCH /api/checklists/<id>`: optional incremental updates for autosave (supports partial payloads).
- `DELETE /api/checklists/<id>`: remove checklist after confirmation.
- `POST /api/checklists/<id>/import`: upload YAML; validates before replacing data.
- `GET /api/checklists/<id>/export`: return YAML (Content-Type text/yaml).
- `GET /api/checklists/<id>/print`: return print-ready HTML; front end opens in new tab and triggers `window.print()`.
- Future: `GET /api/checklists/<id>/pdf`: generate binary PDF if browser print proves insufficient.

### Payload Structure
```
{
  "id": "c123",
  "title": "737NG Normal Checklist",
  "author": "Jane Doe",
  "revision": "1.0",
  "sections": [
    {
      "id": "s1",
      "title": "Preflight",
      "position": 1,
      "items": [
        {
          "id": "i1",
          "left_text": "Oxygen",
          "right_text": "TESTED, 100%",
          "format": {"bold_left": false, "underline_right": false},
          "position": 1
        }
      ]
    }
  ],
  "metadata": {"created_at": "2024-01-01T12:00:00Z", "updated_at": "2024-01-01T12:15:00Z"}
}
```

## YAML Schema
```
version: 1
metadata:
  title: "737-800NG Normal Checklist"
  author: "Jane Doe"
  revision: "1.0"
  created_at: "2024-01-01T12:00:00Z"
  updated_at: "2024-01-01T12:15:00Z"
sections:
  - id: preflight
    title: "PREFLIGHT"
    items:
      - id: oxygen
        left: "Oxygen"
        right: "TESTED, 100%"
        format:
          style: ["uppercase_right"]
      - id: instrument_xfer
        left: "Instrument Xfer & Display Switches"
        right: "NORMAL, AUTO"
```
- Schema enforced via Marshmallow; unknown fields rejected unless flagged for forward compatibility.
- IDs optional on import; backend generates UUIDs when missing.

## Frontend Architecture
- **State store**: lightweight controller holding checklist data, selection, and undo stack (implemented with JavaScript classes and an event emitter pattern).
- **Modules**: `apiClient`, `checklistStore`, `editorView`, `printPreview`, `yamlModal`.
- **Rendering**: Use template literals to render sections and items; DOM diffing via `requestAnimationFrame` updates to minimize reflows.
- **Interactions**: Drag-and-drop ordering implemented with HTML5 draggable API; keyboard shortcuts for undo/redo, print, save.
- **Validation**: Client-side schema check before hitting APIs to surface errors promptly.

## Styling and Layout Strategy
- CSS variables define Boeing palette (blue bars #c3d9ed, black text #000, grey lines).
- CSS Grid for two primary columns; sections stack vertically with consistent gutter.
- Print stylesheet sets page size, margins, and hides controls; ensures each section box stays within column using `page-break-inside: avoid`.
- Provide fallback fonts (Arial Narrow, Helvetica, sans-serif) approximating Boeing typography; allow custom font upload later.

## Workflow Diagrams
1. **Edit Flow**: load checklist -> state store fetch -> user edits -> store updates -> debounced autosave to `/api/checklists/<id>` -> UI toast on success.
2. **Import Flow**: user selects YAML -> frontend parses with `js-yaml` safe loader -> preview diff -> send to `/import` endpoint -> backend validates -> commit transaction -> reload editor.
3. **Print Flow**: user opens print preview -> new route renders static HTML -> window.print -> user saves as PDF.

## Error Handling Strategy
- Backend returns structured JSON: `{ "error": { "code": "validation_error", "details": [...] } }`.
- Client displays toast banner and inline markers on problematic fields.
- Import errors reference offending YAML path and reason.

## Security Considerations
- Enforce single-password Basic Auth via `Authorization` header; password hash stored in Google Secret Manager and exposed to Cloud Run as environment variable `APP_SHARED_PASSWORD_HASH`.
- Use Flask-Talisman or manual headers for basic security (CSP, HSTS when served over HTTPS via Firebase-provisioned certificates).
- Limit upload size and sanitize filenames; store YAML uploads in memory only until parsed.
- CSRF protection via `Flask-WTF` or double-submit tokens for mutating requests; require HTTPS to mitigate credential leakage.

## Testing Strategy
- **Backend**: pytest suite covering services, schema validation, YAML round-trip, and API endpoints (use Flask test client).
- **Frontend**: vitest or Jest for store logic, Playwright smoke tests for editor, import/export, and print view.
- **PDF/Print QA**: snapshot tests comparing rendered HTML to baseline PNG using Playwright screenshot diff.
- **Continuous Integration**: GitHub Actions running lint (ruff + black check), pytest, and frontend tests on push; optional job invoking Firebase emulator tests.

## Deployment Plan
- Author a `Dockerfile` for the Flask app; build via Google Cloud Build triggered by `firebase deploy --only hosting,functions` (or GitHub Actions invoking `gcloud builds submit`).
- Push the image to Artifact Registry and deploy to Cloud Run with minimum instances set to zero (scale-to-zero) and concurrency tuned for workload.
- Configure Firebase Hosting rewrite rules in `firebase.json` to proxy `/api/**` and `/auth/**` to the Cloud Run service (region `us-central1` by default).
- Store secrets (`APP_SHARED_PASSWORD_HASH`, `SECRET_KEY`, database URL) in Google Secret Manager and mount them as Cloud Run environment variables.
- For persistence beyond SQLite, provision Cloud SQL (PostgreSQL) and connect via Cloud SQL Auth Proxy sidecar; configure SQLAlchemy connection string accordingly. For MVP, allow local SQLite, Cloud Run uses Cloud SQL.
- Enable HTTPS through Firebase-managed certificates; add custom domain via Firebase console and update DNS.

## Observability
- Structured logging (JSON) with request IDs. Log imports/exports and error traces to Cloud Logging via standard stdout.
- Health endpoint `/health` returning DB connectivity status.
- Optional Sentry integration for error capture; alternatively use Google Cloud Error Reporting.

## Future Enhancements (Post-MVP)
- Multi-user accounts with permissions and collaboration.
- Checklist version history with diff viewer.
- Template library for other aircraft types.
- Offline-ready PWA mode for inflight use.
- Localization of UI strings and units.
