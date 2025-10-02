# Boeing Checklist Maker MVP

This repository contains a lightweight Boeing-themed checklist editor built with Flask, SQLite, and vanilla JavaScript. It focuses on quick edits, automatic saves, easy duplication, and a print-friendly view.

## What the Webapp Does
- Single-page editor for adding, reordering, and removing checklist sections and items.
- Autosave keeps the latest draft ready when you return to the app.
- Duplicate action spins up a fresh copy when you want a variation without starting over.
- Print preview renders the same two-column layout used in the editor for paper or PDF.

## Using the Editor
1. Open the app and review the default checklist to understand the structure.
2. Rename or add sections to match the flow you need; keep titles short so they fit in the column header.
3. Add checklist items row by row, using the left column for the call-out and the right column for the expected response.
4. Drag items or sections into the order you want, then click Duplicate if you need a branching scenario.
5. Choose Print to open the print-friendly view, adjust scaling if needed, and save to PDF or send to paper.

**Tips for clean checklists**
- Group three to seven items per section to keep lists scannable.
- Start each item with an action verb ("Set", "Verify", "Confirm") for faster readbacks.
- Reserve the right column for short confirmations or target values.
- Do a dry run in the print preview before handing the checklist to others.

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

- Single checklist CRUD backed by SQLite and SQLAlchemy for sections and items.
- Inline section and item editing with drag-to-reorder interactions.
- Autosave and duplicate endpoints that keep the latest draft ready.
- Print-friendly HTML view for quick PDF or paper handouts.
- Optional shared-password gate plus a `/health` endpoint for deploy checks.

See `docs/Task_working.md` for task-level completion tracking.
