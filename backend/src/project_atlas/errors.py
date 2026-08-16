from typing import Any

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
):
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return jsonify({"error": error}), status_code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return _error_response(error.code, error.message, error.status_code, error.details)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        code = error.name.upper().replace(" ", "_")
        message = (
            "The requested resource does not exist."
            if error.code == 404
            else "The request could not be completed."
        )
        return _error_response(code, message, error.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled application error", exc_info=error)
        return _error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred.",
            500,
        )
