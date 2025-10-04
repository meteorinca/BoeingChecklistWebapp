# Moeing Checklist Maker MVP

This repository contains a lightweight Moeing-themed checklist editor backed by Flask, Firestore, and vanilla JavaScript. The editor still focuses on quick edits, automatic saves, easy duplication, and a print-friendly view, but data now lives in Google Cloud Firestore so you can run the stack in Firebase.

## What the Webapp Does
- Single-page editor for adding, reordering, and removing checklist sections and items.
- Autosave keeps the latest draft ready when you return to the app.
- Duplicate action spins up a fresh copy when you want a variation without starting over.
- Print preview renders the same two-column layout used in the editor for paper or PDF.

## Local Development

1. **Create a Python environment & install deps**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # or source .venv/bin/activate on macOS/Linux
   pip install -r backend/requirements.txt
   ```

2. **Provision Firestore credentials**

   - Create a Firebase project (the examples below assume `checklistapp`).
   - Generate a service account key with the **Cloud Datastore User** role and download the JSON file.
   - Point the backend at that key and project ID:

     ```powershell
     $env:GOOGLE_APPLICATION_CREDENTIALS = 'C:\path\to\service-account.json'
     $env:FIRESTORE_PROJECT = 'checklistapp'
     ```

     > Tip: For offline hacking you can run `gcloud beta emulators firestore start --host-port=localhost:8081` and set `FIRESTORE_EMULATOR_HOST=localhost:8081` instead of using a service account.

3. **Set optional auth and Flask variables**

   ```powershell
   python -c "import bcrypt; print(bcrypt.hashpw(b'secret-password', bcrypt.gensalt()).decode())"
   $env:APP_SHARED_PASSWORD_HASH = '<paste-generated-hash>'
   $env:FLASK_APP = 'backend.wsgi:app'
   ```

   If `APP_SHARED_PASSWORD_HASH` is not provided the API remains open (handy for local exploration).

4. **Run the development server**

   ```powershell
   flask run
   ```

5. **Sign in via the frontend**

   Visit http://127.0.0.1:5000. Enter the shared password when prompted (username optional) to start editing. Autosave will trigger ~800 ms after the last change.

## Firebase Deployment Overview

The repo ships with Firebase Hosting + Cloud Run configuration. After you customise the project ID and Cloud Run service name you can deploy with:

```bash
# 1. Authenticate and set project
firebase login
firebase use checklistapp

# 2. Build & deploy the Cloud Run service (uses Dockerfile at repo root)
gcloud builds submit --tag gcr.io/checklistapp/checklist-backend .
gcloud run deploy checklist-backend \
  --image gcr.io/checklistapp/checklist-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 3. Wire Hosting to the Cloud Run instance and upload static assets
firebase deploy --only hosting,firestore:indexes
```

See `docs/how_it_works.md` and `docs/deployment.md` for deeper architecture and rollout notes.

## Project Structure

```
backend/
  app/
    blueprints/    # API and health endpoints
    data/          # Default Moeing checklist seed (YAML)
    services/      # Firestore persistence, import/export helpers
    static/        # SPA assets (HTML, CSS, JS)
    templates/     # Print-ready Jinja template
  requirements.txt
  wsgi.py
Dockerfile         # Container for Cloud Run
firebase.json      # Firebase Hosting rewrites -> Cloud Run
firestore.rules    # Locked-down Firestore access (API only)
```

## Capabilities Implemented

- Single checklist CRUD backed by Firestore documents.
- Inline section and item editing with drag-to-reorder interactions.
- Autosave and duplicate endpoints that keep the latest draft ready.
- Print-friendly HTML view for quick PDF or paper handouts.
- Optional shared-password gate plus a `/health` endpoint for deploy checks.

See `docs/Task_working.md` for current backlog status.
