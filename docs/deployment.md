# Deployment Guide: Moeing Checklist Webapp

This guide summarises the steps required to ship the checklist editor via Firebase Hosting (static assets) and Cloud Run (Flask API).

## Prerequisites
- Firebase project with Firestore enabled (examples assume `checklistapp`).
- `firebase-tools` CLI and `gcloud` CLI installed and authenticated.
- Service account with roles: `Cloud Run Admin`, `Cloud Build Service Account`, `Artifact Registry Writer`, `Cloud Datastore User`.
- Local checkout of this repository with Docker installed (Cloud Build can build remotely).

## 1. Configure Firebase
1. Set the default project for Firebase CLI:
   ```bash
   firebase login
   firebase use checklistapp
   ```
2. Review `.firebaserc` and adjust the project id if needed.
3. Inspect `firebase.json` rewrites and update the Cloud Run `serviceId` and `region` to match your target.

## 2. Build & Deploy Cloud Run
The Dockerfile at repo root bundles the Flask app. You can build locally or let Cloud Build create the image:

```bash
# Submit a Cloud Build to produce the container image
gcloud builds submit --tag gcr.io/checklistapp/checklist-backend .

# Deploy the image to Cloud Run (public HTTPS service)
gcloud run deploy checklist-backend   --image gcr.io/checklistapp/checklist-backend   --platform managed   --region us-central1   --allow-unauthenticated
```

Environment variables to set on the Cloud Run service:
- `APP_ENV=production`
- `APP_SHARED_PASSWORD_HASH=<bcrypt-hash>`
- `FIRESTORE_PROJECT=checklistapp`

Cloud Run automatically mounts credentials, so no need to set `GOOGLE_APPLICATION_CREDENTIALS`.

## 3. Deploy Hosting + Firestore Indexes
After Cloud Run is live, point Firebase Hosting at it and upload static assets:

```bash
firebase deploy --only hosting,firestore:indexes
```

This publishes the editor (from `backend/app/static`) and locks Firestore rules (deny-all by default).

## 4. Verification Checklist
- Visit the Hosting URL (e.g., https://checklistapp.web.app) ? confirm assets load over HTTPS.
- Try the editor workflow: create > edit > duplicate > import YAML > print preview.
- Confirm API calls hit Cloud Run (`gcloud run services proxy checklist-backend` + inspect logs).
- Review Firestore console to ensure documents appear with expected shape.
- Rotate passwords by updating `APP_SHARED_PASSWORD_HASH` in Cloud Run and redeploy if required.

## Optional: Automating Builds
You can register a GitHub Action or Cloud Build trigger that runs the same commands whenever `main` changes. Keep service account keys in Secret Manager and inject them at build time.
