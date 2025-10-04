# Main Design: Boeing Checklist Webapp

## Architecture Snapshot
The MVP runs as a Flask API packaged for Cloud Run. Firebase Hosting serves the static editor while rewrites proxy `/api/*` traffic into the Cloud Run service. Firestore stores checklist documents with embedded sections/items so no extra tables are required.

```
+-----------+        +-----------------+        +----------------+
|  Browser  | <----> |  Firebase Host  | <----> |  Cloud Run     |
|  (SPA)    |        |  + Rewrites     |        |  Flask + GCF   |
+-----------+        +-----------------+        +----------------+
                                                     |
                                                     v
                                               Firestore (documents)
```

## Technology Choices
- Python 3 + Flask for routing, templating, and JSON responses.
- `google-cloud-firestore` SDK for persistence (simple document reads/writes, server-side slug checking).
- Vanilla JS modules plus lightweight DOM helpers for the editor.
- Firebase Hosting + Cloud Run for managed HTTPS hosting without owning infrastructure.

## Data Model
Each checklist document stored in Firestore looks like:

```
{
  id: uuid,
  slug: string,
  title: string,
  author: string | null,
  revision: string | null,
  theme: string,
  sections: [
    {
      id: uuid,
      title: string,
      position: number,
      items: [
        {
          id: uuid,
          left_text: string,
          right_text: string | null,
          format: object,
          position: number
        }
      ]
    }
  ],
  metadata: { title, author, revision, theme, created_at?, updated_at? },
  created_at: timestamp,
  updated_at: timestamp
}
```

No SQL migrations are required; Firestore documents evolve schemalessly by the service layer.

## API Surface
- `GET /api/checklists`: list checklist summaries ordered by `updated_at`.
- `POST /api/checklists`: create a new checklist with default sections/items.
- `GET /api/checklists/{id}`: return a full checklist for editing.
- `PUT /api/checklists/{id}`: replace the checklist payload in Firestore.
- `POST /api/checklists/{id}/import`: import YAML/Markdown into the existing checklist.
- `GET /api/checklists/{id}/export`: return YAML for backup/export.
- `GET /api/checklists/{id}/print`: render HTML for printing.

## Frontend Design
- `app.js` keeps checklist state in memory and renders sections/items with template literals.
- Event listeners on buttons and inputs push updates through a debounced save routine.
- Drag-and-drop for sections/items updates `position` before the next PUT.
- Print preview opens a new window pointed at the print route and immediately calls `window.print()`.

## Styling
- CSS variables define colors and spacing for readability when both editing and printing.
- Theme dropdown drives body `data-theme` attributes; additional themes can be plugged in without changing markup.

## Error Handling
- Backend returns `{ "error": { "message": str } }` envelopes for validation issues (e.g., missing sections, slug conflicts).
- Frontend displays inline banners and keeps the previous state in memory so a failed save can be retried.

## Future-Friendly Hooks
- Introduce per-user storage by namespacing Firestore documents under user IDs once authentication lands.
- Add search or tagging by creating composite indexes on Firestore fields (e.g., `slug`, `updated_at`).
- Swap Firestore for another data store by reimplementing `services/checklists.py` while leaving API and frontend untouched.
