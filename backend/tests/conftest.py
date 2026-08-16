import pytest
from flask import Flask
from flask.testing import FlaskClient

from project_atlas import create_app
from project_atlas.extensions import db


@pytest.fixture()
def app() -> Flask:
    app = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite+pysqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {},
        },
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
