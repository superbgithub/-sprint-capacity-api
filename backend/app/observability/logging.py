"""
Structured logging configuration with correlation IDs and context.
"""
import logging
import sys
import json
import time
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar
from uuid import uuid4

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON with additional context.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': request_id_var.get(),
        }
        
        # Add user_id if present
        user_id = user_id_var.get()
        if user_id:
            log_entry['user_id'] = user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add source location for errors
        if record.levelno >= logging.ERROR:
            log_entry['source'] = {
                'file': record.pathname,
                'line': record.lineno,
                'function': record.funcName,
            }
        
        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # Set log level for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with structured formatting.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields: Any
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **extra_fields: Additional fields to include in log entry
    """
    log_func = getattr(logger, level.lower())
    
    # Create a log record with extra fields
    extra = {'extra_fields': extra_fields} if extra_fields else {}
    log_func(message, extra=extra)


def set_request_id(request_id: str = None) -> str:
    """
    Set the request ID for the current context.
    
    Args:
        request_id: Optional request ID. If not provided, generates a new UUID.
    
    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set the user ID for the current context."""
    user_id_var.set(user_id)


def clear_context() -> None:
    """Clear all context variables."""
    request_id_var.set('')
    user_id_var.set('')
