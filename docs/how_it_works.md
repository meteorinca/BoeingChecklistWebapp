# Boeing Checklist Webapp - How It Works

This guide captures the moving parts of the slimmed-down checklist MVP so you can keep the project running and make lightweight improvements.

## Application Overview
- The app is a single-page interface served by Flask from `backend/app/static/index.html`.
- Users edit one checklist at a time; sections and items are stored in SQLite (`checklists.db`).
- Autosave writes every change straight to the database so the latest draft is always available.
- A print view reuses the same data to show a clean two-column layout before sending to the printer dialog.

```
Browser (vanilla JS)
    |
    +-- GET /api/checklists/current
    +-- PUT /api/checklists/current
    +-- POST /api/checklists/current/duplicate
    +-- GET /api/checklists/current/print

Flask (backend/app)
    |
    +-- SQLAlchemy models backed by SQLite
    +-- Services to map form data <-> database rows
    +-- Simple auth hook for an optional shared password
```

## Backend Highlights
- `backend/app/__init__.py` wires the Flask app, database session, and API blueprint.
- `backend/app/models.py` defines `Checklist`, `Section`, and `Item` tables with ordering fields.
- `backend/app/services/checklists.py` exposes helpers to load the active checklist, persist updates, and duplicate an existing list.
- `backend/app/blueprints/api.py` provides JSON endpoints for the editor and the print view.

## Frontend Highlights
- `backend/app/static/js/app.js` handles local state, renders the checklist, and debounces saves.
- Sections and items are rendered with template strings; buttons call the API through a tiny `apiClient` wrapper.
- The print preview opens `/api/checklists/current/print` in a new tab so the browser print dialog picks up the layout CSS.

## Data Flow
1. On load the SPA requests `GET /api/checklists/current` to hydrate the editor.
2. Edits mutate local state; a short debounce triggers `PUT /api/checklists/current` with the full section/item payload.
3. The duplicate action calls `POST /api/checklists/current/duplicate` and reloads the editor with the copy.
4. Print opens the dedicated HTML view which reads from the same database records.

## Configuration
- `APP_SHARED_PASSWORD_HASH` (optional): bcrypt hash gating access behind one shared password.
- `DATABASE_URL` (optional): point to a different SQLite path if you do not want the default file.
- `SECRET_KEY`: Flask session secret, auto-generated for dev if not supplied.

## Files To Know
| Path | Purpose |
| --- | --- |
| `backend/app/__init__.py` | App factory + blueprint registration |
| `backend/app/models.py` | SQLAlchemy models for checklist data |
| `backend/app/services/checklists.py` | Persistence helpers + duplicate logic |
| `backend/app/static/js/app.js` | Frontend state + autosave |
| `backend/app/templates/print.html` | Print-friendly layout |

## Extending The MVP Safely
- Add more checklist metadata by extending the models and updating the serializer in `services/checklists.py`.
- Introduce per-device backups by exporting the JSON payload and storing it in IndexedDB.
- Layer simple sharing later by adding a `checklists` table keyed by user tokens once authentication needs are clearer.