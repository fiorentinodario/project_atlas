from flask import Blueprint

api_blueprint = Blueprint("api", __name__)

from project_atlas.ai_assistant.routes import assistant_blueprint  # noqa: E402
from project_atlas.analyses import analyses_blueprint  # noqa: E402
from project_atlas.api import routes  # noqa: E402, F401
from project_atlas.auth import auth_blueprint  # noqa: E402
from project_atlas.decisions import decisions_blueprint  # noqa: E402
from project_atlas.documents import documents_blueprint  # noqa: E402
from project_atlas.projects import projects_blueprint  # noqa: E402
from project_atlas.rag.routes import rag_blueprint  # noqa: E402
from project_atlas.tasks import tasks_blueprint  # noqa: E402

api_blueprint.register_blueprint(auth_blueprint)
api_blueprint.register_blueprint(assistant_blueprint)
api_blueprint.register_blueprint(analyses_blueprint)
api_blueprint.register_blueprint(documents_blueprint)
api_blueprint.register_blueprint(decisions_blueprint)
api_blueprint.register_blueprint(projects_blueprint)
api_blueprint.register_blueprint(rag_blueprint)
api_blueprint.register_blueprint(tasks_blueprint)
