"""Logging helper utilities.

Provides convenient functions for getting loggers and managing log context.
"""
import contextvars
from contextlib import contextmanager
from typing import Any, Generator, Optional

import structlog
from app.core.logging import get_logger as _get_logger

# Context variables for request tracing
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
_user_id_var: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "user_id", default=None
)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance with context binding.

    Args:
        name: Logger name, typically __name__ from the calling module

    Returns:
        A configured structlog logger with bound context
    """
    logger = _get_logger(name)

    # Auto-bind context variables if present
    context = {}
    request_id = _request_id_var.get()
    if request_id:
        context["request_id"] = request_id

    user_id = _user_id_var.get()
    if user_id:
        context["user_id"] = user_id

    if context:
        logger = logger.bind(**context)

    return logger


@contextmanager
def log_context(
    request_id: Optional[str] = None,
    user_id: Optional[int] = None,
    **extra: Any
) -> Generator[None, None, None]:
    """Context manager for setting log context.

    Usage:
        with log_context(request_id="abc123", user_id=123):
            logger.info("Processing request")  # Auto-includes context

    Args:
        request_id: Unique request identifier for tracing
        user_id: Current user ID
        **extra: Additional context variables
    """
    tokens = []

    if request_id is not None:
        tokens.append((_request_id_var, _request_id_var.set(request_id)))
    if user_id is not None:
        tokens.append((_user_id_var, _user_id_var.set(user_id)))

    # Bind extra context to structlog
    if extra:
        structlog.contextvars.bind_contextvars(**extra)

    try:
        yield
    finally:
        # Restore context
        for var, token in tokens:
            var.reset(token)
        if extra:
            structlog.contextvars.unbind_contextvars(*extra.keys())


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return _request_id_var.get()


def get_user_id() -> Optional[int]:
    """Get current user ID from context."""
    return _user_id_var.get()


def generate_request_id() -> str:
    """Generate a unique request ID."""
    import uuid
    return f"req_{uuid.uuid4().hex[:12]}"
