from __future__ import annotations

from flask import current_app
from flask_marshmallow import Marshmallow
from google.cloud import firestore


ma = Marshmallow()
_firestore_client: firestore.Client | None = None


def init_firestore(app) -> firestore.Client:
    """Initialise and cache the Firestore client."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client
    project_id = app.config.get("FIRESTORE_PROJECT")
    if project_id:
        client = firestore.Client(project=project_id)
    else:
        client = firestore.Client()
    _firestore_client = client
    return client


def get_firestore() -> firestore.Client:
    """Return the cached Firestore client, initialising it on-demand."""
    global _firestore_client
    if _firestore_client is None:
        app = current_app._get_current_object()
        return init_firestore(app)
    return _firestore_client
