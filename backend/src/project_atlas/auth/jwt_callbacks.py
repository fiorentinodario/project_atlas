from flask_jwt_extended import JWTManager

from project_atlas.errors import _error_response


def register_jwt_callbacks(jwt: JWTManager) -> None:
    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return _error_response("TOKEN_EXPIRED", "The authentication token has expired.", 401)

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return _error_response("INVALID_TOKEN", "The authentication token is invalid.", 401)

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return _error_response("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return _error_response("TOKEN_REVOKED", "The authentication token was revoked.", 401)
