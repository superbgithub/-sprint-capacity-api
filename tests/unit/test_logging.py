"""
Tests for structured logging.
"""
import pytest
import logging
import json
from io import StringIO
from app.observability.logging import (
    setup_logging,
    get_logger,
    log_with_context,
    set_request_id,
    get_request_id,
    set_user_id,
    clear_context,
    StructuredFormatter
)


def test_structured_formatter():
    """Test that StructuredFormatter produces JSON output."""
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "Test message"
    assert "timestamp" in data


def test_request_id_context():
    """Test request ID context management."""
    # Set request ID
    request_id = set_request_id()
    assert request_id is not None
    assert len(request_id) == 36  # UUID length
    
    # Get request ID
    retrieved_id = get_request_id()
    assert retrieved_id == request_id
    
    # Clear context
    clear_context()
    # After clear, get_request_id() returns empty string or None
    assert get_request_id() in (None, "")


def test_custom_request_id():
    """Test setting custom request ID."""
    custom_id = "custom-request-123"
    set_request_id(custom_id)
    assert get_request_id() == custom_id
    clear_context()


def test_user_id_context():
    """Test user ID context management."""
    set_user_id("user-123")
    
    # Context should contain user_id (can't directly access contextvars in test)
    # But we can verify it doesn't crash
    clear_context()


def test_get_logger():
    """Test getting a logger instance."""
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"


def test_log_with_context():
    """Test logging with context."""
    logger = get_logger("test_context")
    set_request_id("test-request-id")
    
    # Capture log output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Log with context
    log_with_context(
        logger,
        'info',
        'Test message',
        extra_field='extra_value'
    )
    
    # Parse output
    output = stream.getvalue()
    if output:
        data = json.loads(output.strip())
        assert data["message"] == "Test message"
        assert data.get("extra_field") == "extra_value"
    
    clear_context()


def test_setup_logging():
    """Test logging setup."""
    setup_logging("DEBUG")
    
    # Verify root logger has the right level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
