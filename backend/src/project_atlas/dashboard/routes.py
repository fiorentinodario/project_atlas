from uuid import UUID

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from project_atlas.dashboard.service import dashboard_data

dashboard_blueprint = Blueprint("dashboard", __name__)


@dashboard_blueprint.get("/dashboard")
@jwt_required(locations=["headers"])
def show():
    return jsonify({"data": dashboard_data(UUID(get_jwt_identity()))})
