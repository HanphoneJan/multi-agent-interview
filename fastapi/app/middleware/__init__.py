"""Middleware Configuration"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.core.constants import GZIP_MINIMUM_SIZE
from app.middleware.logging import RequestLoggingMiddleware
from app.utils.log_helper import get_logger

logger = get_logger("middleware")


def setup_middleware(app):
    """Setup all middleware"""
    settings = get_settings()

    # Log CORS configuration for debugging
    logger.info(
        "Configuring CORS middleware",
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    )

    # CORS Middleware
    # Note: When allow_credentials=True, allow_headers cannot be ["*"]
    # We need to explicitly list allowed headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Accept-Language",
            "Content-Language",
            "X-Requested-With",
            "Origin",
        ],
        expose_headers=["Content-Range", "X-Request-ID"],
        max_age=600,  # Cache preflight for 10 minutes
    )

    # Gzip Middleware
    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MINIMUM_SIZE)

    # Request Logging Middleware (structured logging with request_id)
    app.add_middleware(RequestLoggingMiddleware)

    # Global Exception Handler - must add CORS headers manually
    # because exception responses bypass CORS middleware
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", error=str(exc))

        # Get origin from request
        origin = request.headers.get("origin", "")

        # Determine allowed origin
        # In DEBUG mode, allow any localhost origin for development
        cors_origin = None
        if settings.DEBUG and ("localhost" in origin or "127.0.0.1" in origin):
            cors_origin = origin
        elif origin in settings.CORS_ORIGINS:
            cors_origin = origin
        elif settings.CORS_ORIGINS:
            cors_origin = settings.CORS_ORIGINS[0]
        else:
            cors_origin = "*"

        # Build response headers with CORS
        headers = {
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true" if settings.CORS_ALLOW_CREDENTIALS else "false",
            "Access-Control-Expose-Headers": "Content-Range, X-Request-ID",
        }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.DEBUG else "An error occurred"
            },
            headers=headers
        )
