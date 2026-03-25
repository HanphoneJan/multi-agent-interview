"""Custom exceptions for the application"""
from typing import Any


class BaseAPIError(Exception):
    """Base API exception"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str | None = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundError(BaseAPIError):
    """Resource not found exception"""

    def __init__(self, detail: str = "Resource not found", error_code: str | None = None):
        super().__init__(status_code=404, detail=detail, error_code=error_code)


class UnauthorizedError(BaseAPIError):
    """Unauthorized exception"""

    def __init__(self, detail: str = "Unauthorized", error_code: str | None = None):
        super().__init__(status_code=401, detail=detail, error_code=error_code)


class ForbiddenError(BaseAPIError):
    """Forbidden exception"""

    def __init__(self, detail: str = "Forbidden", error_code: str | None = None):
        super().__init__(status_code=403, detail=detail, error_code=error_code)


class ValidationError(BaseAPIError):
    """Validation error exception"""

    def __init__(self, detail: str = "Validation failed", error_code: str | None = None):
        super().__init__(status_code=422, detail=detail, error_code=error_code)


class ConflictError(BaseAPIError):
    """Conflict exception (e.g., duplicate resource)"""

    def __init__(self, detail: str = "Resource conflict", error_code: str | None = None):
        super().__init__(status_code=409, detail=detail, error_code=error_code)


class InternalServerError(BaseAPIError):
    """Internal server error exception"""

    def __init__(self, detail: str = "Internal server error", error_code: str | None = None):
        super().__init__(status_code=500, detail=detail, error_code=error_code)
