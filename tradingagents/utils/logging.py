"""
Structured Logging System

This module provides a centralized logging system with structured output,
log levels, and proper formatting for production use.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for logs.

    Outputs logs in JSON format with consistent fields for easy parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "symbol"):
            log_data["symbol"] = record.symbol
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for human-readable logs.

    Uses ANSI color codes for different log levels.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Get color for this level
        color = self.COLORS.get(record.levelname, '')

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build message
        msg = f"{color}{self.BOLD}[{record.levelname}]{self.RESET} "
        msg += f"{timestamp} "
        msg += f"{color}{record.name}:{record.funcName}{self.RESET} "
        msg += f"- {record.getMessage()}"

        # Add exception if present
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)

        return msg


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    use_json: bool = False,
    use_colors: bool = True
) -> None:
    """
    Setup centralized logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        use_json: Whether to use JSON format (default: False for console, True for file)
        use_colors: Whether to use colored output for console (default: True)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if use_json:
        console_formatter = StructuredFormatter()
    elif use_colors and sys.stdout.isatty():
        console_formatter = ColoredConsoleFormatter()
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)

        # Always use JSON for file logs
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Log initial message
    root_logger.info(
        f"Logging initialized (level={level}, "
        f"file={log_file if log_file else 'none'})"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding extra fields to log records.

    Usage:
        with LogContext(symbol="AAPL", agent="technical"):
            logger.info("Analysis complete")
    """

    def __init__(self, **kwargs):
        """
        Initialize log context.

        Args:
            **kwargs: Extra fields to add to log records
        """
        self.extra = kwargs
        self.old_factory = None

    def __enter__(self):
        """Enter context."""
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.extra.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


def log_execution_time(logger: logging.Logger):
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time(logger)
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(
                    f"{func.__name__} completed in {elapsed:.3f}s"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.3f}s: {str(e)}"
                )
                raise
        return wrapper
    return decorator
