from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from ..services import checklists as service
from ..utils.auth import require_basic_auth

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _json_response(data, status: int = 200):
    return jsonify({"data": data}), status


@api_bp.errorhandler(service.ChecklistNotFoundError)
def handle_not_found(exc: service.ChecklistNotFoundError):
    return jsonify({"error": {"code": "not_found", "message": str(exc)}}), 404


@api_bp.errorhandler(service.ChecklistConflictError)
def handle_conflict(exc: service.ChecklistConflictError):
    return (
        jsonify({"error": {"code": "conflict", "message": "Checklist title already exists"}}),
        409,
    )


@api_bp.route("/checklists", methods=["GET"])
@require_basic_auth
def list_checklists():
    checklists = [c.to_dict() for c in service.list_checklists()]
    return _json_response(checklists)


@api_bp.route("/checklists", methods=["POST"])
@require_basic_auth
def create_checklist():
    payload = request.get_json(force=True, silent=True) or {}
    checklist = service.create_checklist(payload, author_override=_request_user())
    return _json_response(checklist.to_dict(), status=201)


@api_bp.route("/checklists/<checklist_id>", methods=["GET"])
@require_basic_auth
def retrieve_checklist(checklist_id: str):
    checklist = service.get_checklist(checklist_id)
    return _json_response(checklist.to_dict())


@api_bp.route("/checklists/<checklist_id>", methods=["PUT"])
@require_basic_auth
def replace_checklist(checklist_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    checklist = service.update_checklist(checklist_id, payload, author_override=_request_user())
    return _json_response(checklist.to_dict())


@api_bp.route("/checklists/<checklist_id>", methods=["PATCH"])
@require_basic_auth
def patch_checklist(checklist_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    checklist = service.patch_checklist(checklist_id, payload)
    return _json_response(checklist.to_dict())


@api_bp.route("/checklists/<checklist_id>", methods=["DELETE"])
@require_basic_auth
def remove_checklist(checklist_id: str):
    service.delete_checklist(checklist_id)
    return "", 204


@api_bp.route("/checklists/<checklist_id>/export", methods=["GET"])
@require_basic_auth
def export_checklist(checklist_id: str):
    checklist = service.get_checklist(checklist_id)
    yaml_text = service.export_checklist_to_yaml(checklist)
    return Response(yaml_text, mimetype="text/yaml")


@api_bp.route("/checklists/<checklist_id>/import", methods=["POST"])
@require_basic_auth
def import_checklist(checklist_id: str):
    yaml_text = request.data.decode("utf-8")
    checklist = service.import_checklist_from_yaml(checklist_id, yaml_text)
    return _json_response(checklist.to_dict())


@api_bp.route("/checklists/import", methods=["POST"])
@require_basic_auth
def import_new_checklist():
    yaml_text = request.data.decode("utf-8")
    checklist = service.import_checklist_from_yaml(None, yaml_text)
    return _json_response(checklist.to_dict(), status=201)


@api_bp.route("/checklists/<checklist_id>/print", methods=["GET"])
@require_basic_auth
def print_checklist(checklist_id: str):
    checklist = service.get_checklist(checklist_id)
    return render_template("print.html", checklist=checklist)


def _request_user() -> str | None:
    return request.environ.get("checklist.user")
