from flask import Blueprint

api_blueprint = Blueprint("api", __name__)

from project_atlas.api import routes  # noqa: E402, F401
