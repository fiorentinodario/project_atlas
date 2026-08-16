from typing import Any

from flask import Flask
from flask_cors import CORS

from project_atlas.__version__ import __version__
from project_atlas.api import api_blueprint
from project_atlas.config import config_by_name
from project_atlas.errors import register_error_handlers


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

    if config_name == "production" and app.config["SECRET_KEY"] == "development-only-secret":
        raise RuntimeError("SECRET_KEY must be set in the production environment")

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    app.register_blueprint(api_blueprint, url_prefix="/api/v1")
    register_error_handlers(app)

    return app


__all__ = ["__version__", "create_app"]
