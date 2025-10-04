from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, Response, send_from_directory

from .blueprints.api import api_bp
from .blueprints.health import health_bp
from .config import get_config
from .extensions import init_firestore, ma
from .services.checklists import ensure_seed_data


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    env_name = config_name or os.getenv("FLASK_ENV") or os.getenv("APP_ENV")
    app.config.from_object(get_config(env_name))

    configure_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_routes(app)

    with app.app_context():
        init_firestore(app)
        template_path = Path(app.config["TEMPLATE_SEED_PATH"]) if app.config.get("TEMPLATE_SEED_PATH") else None
        if template_path and app.config.get("ENABLE_DEFAULT_SEED", False):
            ensure_seed_data(template_path)

    return app


def configure_logging(app: Flask) -> None:
    if app.debug:
        return
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)


def register_extensions(app: Flask) -> None:
    ma.init_app(app)
    init_firestore(app)


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(api_bp)
    app.register_blueprint(health_bp)


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index() -> Response:
        return app.send_static_file("index.html")

    @app.route("/assets/<path:filename>")
    def serve_static_asset(filename: str) -> Response:
        return send_from_directory(app.static_folder, filename)
