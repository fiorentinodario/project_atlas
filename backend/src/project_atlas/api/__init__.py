from flask import Blueprint

api_blueprint = Blueprint("api", __name__)

from project_atlas.api import routes  # noqa: E402, F401
from project_atlas.auth import auth_blueprint  # noqa: E402
from project_atlas.documents import documents_blueprint  # noqa: E402
from project_atlas.projects import projects_blueprint  # noqa: E402
from project_atlas.tasks import tasks_blueprint  # noqa: E402

api_blueprint.register_blueprint(auth_blueprint)
api_blueprint.register_blueprint(documents_blueprint)
api_blueprint.register_blueprint(projects_blueprint)
api_blueprint.register_blueprint(tasks_blueprint)
