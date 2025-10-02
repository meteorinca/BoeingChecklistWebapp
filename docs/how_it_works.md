# Boeing Checklist Maker — How It Works

This document explains the moving pieces of the Boeing Checklist Maker MVP so you can operate, extend, or debug the project with confidence.

## Application Overview

The app is a single-page editor served by Flask. Static assets (HTML, CSS, JS) live under `backend/app/static`, while REST endpoints power data persistence, YAML import/export, and the print-friendly view. The frontend talks to the backend using JSON over the `/api` namespace.

```
Browser (JS SPA)
       ¦
       +-- GET/POST/PATCH `/api/checklists/**`
       +-- GET `/api/checklists/<id>/export`
       +-- POST `/api/checklists/<id>/import`
       +-- GET `/api/checklists/<id>/print`

Flask (backend/app)
       ¦
       +-- SQLAlchemy models (SQLite by default)
       +-- Checklist services (CRUD + YAML)
       +-- Auth middleware (single shared password)
```

## Backend Details

- **App factory**: `backend/app/__init__.py` wires configuration, extensions, blueprints, static files, and the template seed loader.
- **Database**: SQLite (`checklists.db`) via SQLAlchemy. Models live in `backend/app/models.py` and include `Checklist`, `Section`, and `Item` plus ordering metadata.
- **Auth**: `backend/app/utils/auth.py` enforces single-password Basic Auth using the env var `APP_SHARED_PASSWORD_HASH` (bcrypt hash). Missing hashes log a warning and skip enforcement for local dev.
- **Services**: `backend/app/services/checklists.py` centralizes CRUD, slug generation, autosave-friendly updates, YAML import/export, and template seeding.
- **Blueprints**: The API lives in `backend/app/blueprints/api.py`; health checks sit in `backend/app/blueprints/health.py`.
- **Print view**: `backend/app/templates/print.html` renders a two-column Boeing-style layout and triggers `window.print()`.

## Frontend Details

- **Entry point**: `backend/app/static/index.html` renders the SPA shell.
- **Styles**: `backend/app/static/css/styles.css` defines layout, palettes, and theme skins.
- **Logic**: `backend/app/static/js/app.js` implements the state store (undo/redo + autosave), API client, UI rendering, YAML import/export, print launch, and theme handling.
- **Authentication**: A modal prompts for the shared password; credentials are stored client-side as an Authorization header for subsequent requests.

### Data Flow

1. On login the SPA calls `GET /api/checklists` to load metadata.
2. Selecting a checklist fetches `GET /api/checklists/<id>` and hydrates the store.
3. Edits mutate the local store; after 800?ms of inactivity a PUT `/api/checklists/<id>` persists the full payload.
4. YAML export/download uses `GET /api/checklists/<id>/export`; import pipes the YAML straight to `/api/checklists/<id>/import`.
5. The print button opens `/api/checklists/<id>/print` in a new tab and triggers `window.print()`.

### Theming

Themes are stored with each checklist (`theme` attribute) and applied by toggling a `data-theme` attribute on `<body>`. CSS variables define colors, fonts, and backgrounds for each theme. See `THEMES` inside `app.js` for the available skins.

## Running Locally

```powershell
# from c:\Users\Mna\Documents\PythonCursBalls
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
$env:APP_SHARED_PASSWORD_HASH = '<bcrypt-hash>'
python backend/wsgi.py
```

Visit http://127.0.0.1:5000/, sign in with the shared credentials, and start editing.

## Key Environment Variables

- `APP_SHARED_PASSWORD_HASH`: bcrypt hash of the shared password (required for auth in non-dev).
- `SECRET_KEY`: Flask secret key (defaults to a dev value).
- `DATABASE_URL`: override SQLite with a different database.
- `TEMPLATE_SEED_PATH`: path to the default Boeing YAML seed.

## Files To Know

| Path | Purpose |
| --- | --- |
| `backend/app/__init__.py` | Flask app factory and bootstrap logic |
| `backend/app/models.py` | SQLAlchemy models |
| `backend/app/services/checklists.py` | Business rules, YAML adapters |
| `backend/app/static/index.html` | SPA shell |
| `backend/app/static/css/styles.css` | Styling (+ theme definitions) |
| `backend/app/static/js/app.js` | Frontend state/store, UI, API integration |
| `backend/app/templates/print.html` | Print/PDF layout |
| `docs/how_it_works.md` | This guide |

## Extending The Project

- **More Themes**: Add palette + font variables in CSS (`[data-theme="<name>"]`) and register the theme object inside `app.js`.
- **New Fields**: Update the SQLAlchemy models, Marshmallow schemas, services, and SPA state handling.
- **Deployments**: Add Dockerfile, CI, Firebase/Cloud Run configs per the requirements in `docs/PRD.md` and `docs/master_design.md`.

Happy flying! ??
