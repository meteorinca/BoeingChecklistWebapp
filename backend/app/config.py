import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "sqlite:///" + os.path.join(BASE_DIR, "checklists.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    # Debounce window to inform frontend autosave timing if needed
    AUTOSAVE_DEBOUNCE_MS = int(os.getenv("AUTOSAVE_DEBOUNCE_MS", "800"))
    BASIC_AUTH_REALM = "Boeing Checklist Maker"
    SESSION_COOKIE_SECURE = False  # Overridden in production config
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    TEMPLATE_SEED_PATH = os.getenv("TEMPLATE_SEED_PATH") or os.path.join(DATA_DIR, "boeing_template.yaml")
    ENABLE_DEFAULT_SEED = os.getenv("ENABLE_DEFAULT_SEED", "1") == "1"


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True


CONFIG_MAP = {
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": Config,
}


def get_config(name: str | None) -> type[Config]:
    if not name:
        return Config
    return CONFIG_MAP.get(name, Config)
