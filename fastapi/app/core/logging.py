"""Logging configuration for FastAPI application.

This module configures structlog and standard library logging
to provide structured, production-ready logs.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import structlog
from pythonjsonlogger import jsonlogger

from app.config import get_settings


def setup_logging() -> None:
    """Configure application logging.

    Sets up both structlog and standard library logging with:
    - Console output for development
    - File output with rotation
    - JSON formatting for production/ops
    """
    settings = get_settings()

    # Ensure log directory exists
    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    if settings.LOG_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler (rotating)
    app_log_path = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    if settings.LOG_JSON_FORMAT:
        # JSON formatter for structured logs
        file_formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"timestamp": "timestamp", "level": "level", "name": "logger"}
        )
    else:
        # Plain text formatter
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error log file (always text, separate from main log)
    error_log_path = os.path.join(log_dir, "error.log")
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s\n%(exc_info)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, typically __name__ from the calling module

    Returns:
        A configured structlog logger
    """
    return structlog.get_logger(name)
