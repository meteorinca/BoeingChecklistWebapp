# Boeing Checklist Webapp - How It Works

This guide captures the moving parts of the Firestore-backed checklist MVP so you can keep the project running and make lightweight improvements.

## Application Overview
- The app is a single-page interface served from `backend/app/static/index.html`.
- Flask runs on Cloud Run (or locally) and exposes JSON endpoints plus the print template.
- Firestore stores each checklist document with embedded sections and items.
- Autosave writes every change to Firestore so the latest draft is always available from any device.

```
Browser (vanilla JS)
    |
    +-- GET /api/checklists
    +-- GET/PUT /api/checklists/{id}
    +-- POST /api/checklists/{id}/import
    +-- GET /api/checklists/{id}/print

Flask (Cloud Run)
    |
    +-- Firestore document CRUD (google-cloud-firestore)
    +-- YAML/Markdown import-export service helpers
    +-- Optional basic-auth gate for shared password access
```

## Backend Highlights
- `backend/app/__init__.py` wires the Flask app, Firestore client, and API blueprint.
- `backend/app/services/checklists.py` marshals payloads, enforces slug uniqueness, and persists nested sections/items in Firestore.
- `backend/app/blueprints/api.py` returns JSON envelopes consumed by the editor and print view.
- `backend/wsgi.py` doubles as the Cloud Run entrypoint (served with Gunicorn via the Dockerfile).

## Frontend Highlights
- `backend/app/static/js/app.js` keeps local state, renders the checklist, and debounces saves.
- Sections and items are rendered with template strings; buttons call the API through a tiny `API` wrapper.
- The print preview opens `/api/checklists/{id}/print` in a new tab so the browser print dialog picks up the layout CSS.

## Data Flow
1. On load the SPA requests `GET /api/checklists` to hydrate the list sidebar and opens the most recent checklist.
2. Edits mutate local state; a short debounce triggers `PUT /api/checklists/{id}` with the full section/item payload.
3. Duplicate/import actions reuse the same service layer, creating or replacing the Firestore document.
4. Print opens the dedicated HTML view which reads directly from the Firestore-backed payload.

## Configuration
- `APP_SHARED_PASSWORD_HASH` (optional): bcrypt hash gating access behind one shared password.
- `FIRESTORE_PROJECT`: explicit project ID (falls back to Firebase/GCP environment variables).
- `GOOGLE_APPLICATION_CREDENTIALS`: path to the service-account JSON for local development.
- `FIRESTORE_EMULATOR_HOST` (optional): point at a running emulator instead of Google Cloud.

## Files To Know
| Path | Purpose |
| --- | --- |
| `backend/app/__init__.py` | App factory + Firestore wiring |
| `backend/app/services/checklists.py` | Firestore persistence + import/export logic |
| `backend/app/static/js/app.js` | Frontend state + autosave |
| `backend/app/templates/print.html` | Print-friendly layout |
| `Dockerfile` | Cloud Run container definition |
| `firebase.json` | Hosting rewrites and static asset rules |

## Extending The MVP Safely
- Add more checklist metadata by extending the Firestore document schema in one place (`services/checklists.py`).
- Introduce Firestore security rules for user-level access once auth requirements firm up.
- Layer richer permissions or multi-user support by partitioning documents per account.
