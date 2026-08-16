from pathlib import Path
from typing import Any

from flask import Flask
from flask_cors import CORS

from project_atlas import models  # noqa: F401
from project_atlas.__version__ import __version__
from project_atlas.api import api_blueprint
from project_atlas.auth.jwt_callbacks import register_jwt_callbacks
from project_atlas.config import config_by_name
from project_atlas.errors import register_error_handlers
from project_atlas.extensions import db, jwt, migrate
from project_atlas.rag.providers import build_embedding_provider


def create_app(
    config_name: str = "development",
    config_override: dict[str, Any] | None = None,
) -> Flask:
    """Create and configure an isolated Flask application instance."""
    app = Flask(__name__)

    config_class = config_by_name.get(config_name)
    if config_class is None:
        raise ValueError(f"Unknown configuration: {config_name}")

    app.config.from_object(config_class)
    if config_override:
        app.config.from_mapping(config_override)
    if not app.config["UPLOAD_FOLDER"]:
        app.config["UPLOAD_FOLDER"] = str(Path(app.instance_path) / "uploads")

    if config_name == "production":
        insecure_keys = {
            "SECRET_KEY": "development-only-secret",
            "JWT_SECRET_KEY": "development-only-jwt-secret-change-me",
        }
        missing_keys = [key for key, default in insecure_keys.items() if app.config[key] == default]
        if missing_keys:
            raise RuntimeError(f"Production secrets must be set: {', '.join(missing_keys)}")

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    db.init_app(app)
    jwt.init_app(app)
    register_jwt_callbacks(jwt)
    migrate.init_app(app, db)
    app.extensions["embedding_provider"] = build_embedding_provider(app.config)

    app.register_blueprint(api_blueprint, url_prefix="/api/v1")
    register_error_handlers(app)

    return app


__all__ = ["__version__", "create_app"]
