"""Request logging middleware.

Logs all incoming requests with timing, status codes, and request IDs.
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.log_helper import get_logger, log_context, generate_request_id

logger = get_logger("middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with structured data."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = generate_request_id()

        # Add request ID to response headers
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log request start
        client_host = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method

        with log_context(request_id=request_id):
            logger.info(
                "Request started",
                method=method,
                path=path,
                client=client_host,
                user_agent=request.headers.get("user-agent", "unknown")
            )

            try:
                response = await call_next(request)
                duration_ms = (time.time() - start_time) * 1000

                # Log request completion
                logger.info(
                    "Request completed",
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2)
                )

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id

                return response

            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000

                # Log error
                logger.exception(
                    "Request failed",
                    method=method,
                    path=path,
                    duration_ms=round(duration_ms, 2),
                    error=str(exc)
                )

                # Re-raise the exception to let FastAPI's exception handlers deal with it
                # CORS headers will be added by the exception handler or CORS middleware
                raise
