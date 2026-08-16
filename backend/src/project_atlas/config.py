import os


def _cors_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-secret")
    JSON_SORT_KEYS = False
    CORS_ORIGINS = _cors_origins()
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "testing-secret"


class ProductionConfig(BaseConfig):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
