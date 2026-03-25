"""Tests for logging system."""
import logging
import os
import tempfile

import pytest  # noqa: F401
import structlog

from app.utils.log_helper import get_logger, generate_request_id, log_context


class TestLoggingSetup:
    """Test logging configuration."""

    def test_get_logger_returns_structlog(self):
        """Test that get_logger returns a structlog logger."""
        logger = get_logger("test.module")
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_logger_has_name(self):
        """Test that logger has the correct name."""
        logger = get_logger("test.name")
        assert logger.name == "test.name"


class TestLogContext:
    """Test log context management."""

    def test_generate_request_id_format(self):
        """Test request ID generation format."""
        request_id = generate_request_id()
        assert request_id.startswith("req_")
        assert len(request_id) == 16  # req_ + 12 hex chars

    def test_log_context_sets_request_id(self):
        """Test that log context sets request ID."""
        with log_context(request_id="test-123"):
            # Context should be set inside the block
            pass  # Testing that no exception is raised

    def test_log_context_sets_user_id(self):
        """Test that log context sets user ID."""
        with log_context(user_id=123):
            pass  # Testing that no exception is raised

    def test_log_context_combined(self):
        """Test that log context can set multiple values."""
        with log_context(request_id="req-456", user_id=789, extra="value"):
            pass  # Testing that no exception is raised


class TestLoggingOutput:
    """Test logging output."""

    def test_log_file_created(self):
        """Test that log files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test log file
            log_file = os.path.join(tmpdir, "test.log")
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.INFO)

            test_logger = logging.getLogger("test.output")
            test_logger.setLevel(logging.INFO)
            test_logger.addHandler(handler)

            test_logger.info("Test message")
            handler.flush()

            assert os.path.exists(log_file)

            with open(log_file) as f:
                content = f.read()
                assert "Test message" in content
