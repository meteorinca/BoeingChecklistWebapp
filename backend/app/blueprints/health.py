from __future__ import annotations

from flask import Blueprint, jsonify

from ..extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health() -> tuple[dict, int]:
    try:
        db.session.execute(db.select(1))
        status = {"status": "ok"}
        return status, 200
    except Exception as exc:  # pragma: no cover - defensive guard
        return {"status": "error", "detail": str(exc)}, 503
