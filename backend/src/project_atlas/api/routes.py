from flask import jsonify

from project_atlas import __version__
from project_atlas.api import api_blueprint


@api_blueprint.get("/health")
def health_check():
    return jsonify(
        {
            "data": {
                "service": "project-atlas-api",
                "status": "healthy",
                "version": __version__,
            }
        }
    )
