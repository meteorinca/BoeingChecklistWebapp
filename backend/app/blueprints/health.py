from __future__ import annotations

from flask import Blueprint, jsonify

from ..extensions import get_firestore

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health() -> tuple[dict, int]:
    try:
        # Test Firestore connection instead of SQLAlchemy
        firestore_client = get_firestore()
        # Simple test to verify Firestore is accessible
        collections = list(firestore_client.collections())
        status = {"status": "ok", "firestore": "connected"}
        return status, 200
    except Exception as exc:  # pragma: no cover - defensive guard
        return {"status": "error", "detail": str(exc)}, 503
