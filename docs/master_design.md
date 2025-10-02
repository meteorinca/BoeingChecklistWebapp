# Master Design: Boeing Checklist Webapp

## Architecture Snapshot
The MVP runs as a single Flask service that serves both the editor assets and a tiny JSON API. SQLite stores one active checklist plus its sections and items. The browser renders the editor with vanilla JavaScript and keeps its state synced with the backend through straightforward REST calls.

```
+-----------+        +-------------+        +-------------+
|  Browser  | <----> |   Flask     | <----> |   SQLite    |
|  (SPA)    |        |  API + SPA  |        |  checklists |
+-----------+        +-------------+        +-------------+
```

## Technology Choices
- Python 3 + Flask for routing, templating, and JSON responses.
- SQLAlchemy ORM on top of SQLite for simple persistence.
- Vanilla JS modules plus lightweight DOM helpers for the editor.
- Bootstrap-style utility classes from a small custom CSS file.

## Data Model
- `checklists`: id (uuid), title, created_at, updated_at.
- `sections`: id (uuid), checklist_id, title, position.
- `items`: id (uuid), section_id, left_text, right_text, position.

No migrations are required for the MVP; the database is created on first run from SQLAlchemy metadata.

## API Surface
- `GET /api/checklists/current`: return the stored checklist with sections/items.
- `PUT /api/checklists/current`: replace checklist, section, and item data in a single payload.
- `POST /api/checklists/current/duplicate`: clone the current checklist with a new id and timestamp.
- `GET /api/checklists/current/print`: render HTML that mirrors the print layout.

Responses share the same JSON shape so the frontend can reuse parsing logic.

## Frontend Design
- `app.js` keeps checklist state in memory and renders sections/items with template literals.
- Event listeners on buttons and inputs push updates through a debounced save routine.
- Drag-and-drop for sections/items uses the browser `dragstart`/`drop` events and updates `position` before saving.
- Print preview opens a new window pointed at the print route and immediately calls `window.print()`.

## Styling
- CSS variables define colors and spacing for readability when both editing and printing.
- A dedicated print stylesheet hides controls and ensures two columns fit comfortably on letter or A4 paper.
- Optional dark theme swaps background/text variables without altering layout rules.

## Error Handling
- Backend returns `{ "error": { "message": str } }` envelopes for validation issues.
- Frontend displays inline banners and keeps the previous state in memory so a failed save can be retried.

## Future-Friendly Hooks
- Introduce additional checklist fields by extending the shared serializer in one place.
- Add cloud sync later by swapping SQLite with a remote database through SQLAlchemy connection strings.
- Layer richer permissions behind the existing auth hook once user requirements expand.