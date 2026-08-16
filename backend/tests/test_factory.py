import pytest

from project_atlas import create_app


def test_factory_rejects_unknown_configuration() -> None:
    with pytest.raises(ValueError, match="Unknown configuration"):
        create_app("unknown")


def test_production_requires_explicit_secret() -> None:
    with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
        create_app("production")


def test_production_accepts_explicit_secret() -> None:
    app = create_app("production", {"SECRET_KEY": "production-test-secret"})

    assert app.config["DEBUG"] is False
