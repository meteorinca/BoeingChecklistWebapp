# Boeing Checklist Maker MVP

This repository contains a minimal vertical slice of the Boeing Checklist Maker described in the product and design docs. It includes a Flask backend with SQLite persistence, YAML import/export, a print-ready template, and a vanilla JavaScript single-page editor with autosave.

## Local development

1. **Install dependencies**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

2. **Set environment variables**

   ```powershell
   # Generate a bcrypt hash for your shared password (run once)
   python -c "import bcrypt; print(bcrypt.hashpw(b'secret-password', bcrypt.gensalt()).decode())"

   $env:APP_SHARED_PASSWORD_HASH = '<paste-generated-hash>'
   $env:FLASK_APP = 'backend.wsgi:app'
   ```

   If `APP_SHARED_PASSWORD_HASH` is not provided the API is left open (handy for local exploration).

3. **Run the development server**

   ```powershell
   flask run
   ```

4. **Sign in via the frontend**

   Visit http://127.0.0.1:5000. Enter the shared password when prompted (username optional) to start editing. Autosave will trigger 800?ms after the last change.

## Project structure

```
backend/
  app/
    blueprints/    # API and health endpoints
    data/          # Default Boeing checklist seed (YAML)
    services/      # Business logic for CRUD/YAML
    static/        # SPA assets (HTML, CSS, JS)
    templates/     # Print-ready Jinja template
  requirements.txt
  wsgi.py
```

## Capabilities implemented

- Checklist CRUD with SQLite + SQLAlchemy models for checklists, sections, and items.
- YAML import/export with schema normalization.
- Theme switcher (Boeing + Sticky Note) with per-checklist persistence.
- Single-password Basic Auth check backed by bcrypt hashes.
- Autosave-ready PUT endpoint and PATCH placeholder for future diffing.
- Print-ready HTML view aligned with Boeing visual cues.
- SPA editor: state store with undo/redo, section/item management, YAML import/export, and Boeing-themed styling.
- Health endpoint for deploy readiness checks.

See `docs/Task_working.md` for task-level completion tracking.
