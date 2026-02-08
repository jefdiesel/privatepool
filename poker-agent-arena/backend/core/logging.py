"""Structured logging configuration for the application.

Provides JSON-formatted logs with correlation IDs for request tracing.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set the correlation ID for the current context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    correlation_id_var.set(correlation_id)
    return correlation_id


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add location info
        log_data["location"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        extra_keys = set(record.__dict__.keys()) - {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }
        for key in extra_keys:
            log_data[key] = getattr(record, key)

        return json.dumps(log_data)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for development."""
        color = self.COLORS.get(record.levelname, "")
        correlation_id = get_correlation_id()
        cid_str = f"[{correlation_id}] " if correlation_id else ""

        timestamp = datetime.now(UTC).strftime("%H:%M:%S.%f")[:-3]

        message = (
            f"{color}{timestamp} {record.levelname:8}{self.RESET} "
            f"{cid_str}{record.name}: {record.getMessage()}"
        )

        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON format; otherwise use human-readable format
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter based on environment
    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(DevelopmentFormatter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra fields to logs."""

    def __init__(self, logger: logging.Logger, **kwargs: Any):
        """Initialize log context.

        Args:
            logger: Logger instance
            **kwargs: Extra fields to add to all logs in this context
        """
        self.logger = logger
        self.extra = kwargs

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self.logger.debug(msg, extra={**self.extra, **kwargs})

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self.logger.info(msg, extra={**self.extra, **kwargs})

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self.logger.warning(msg, extra={**self.extra, **kwargs})

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self.logger.error(msg, extra={**self.extra, **kwargs})

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception message with context."""
        self.logger.exception(msg, extra={**self.extra, **kwargs})
