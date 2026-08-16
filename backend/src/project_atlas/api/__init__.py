from flask import Blueprint

api_blueprint = Blueprint("api", __name__)

from project_atlas.api import routes  # noqa: E402, F401
from project_atlas.auth import auth_blueprint  # noqa: E402

api_blueprint.register_blueprint(auth_blueprint)
