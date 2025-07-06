import logging
import os
import json
from functools import wraps
from flask import request, g
import traceback

"""
Logging Configuration

This module provides a comprehensive logging system with the following features:
- Separate log files for different log levels (app.log, debug.log, error.log)
- Context-aware logging with additional metadata
- Configurable log levels via environment variables

Environment Variables:
- APP_LOG_LEVEL: Log level for app.log (default: INFO)
- DEBUG_LOG_LEVEL: Log level for debug.log (default: DEBUG) 
- ERROR_LOG_LEVEL: Log level for error.log (default: ERROR)

Log Files:
- logs/app.log: General application logs (INFO and above by default)
- logs/debug.log: Debug-level logs (DEBUG and above)
- logs/error.log: Error-level logs (ERROR and above)

Usage:
    from app.logging_utils import debug, info, warning, error, critical
    
    debug("Debug message", user_id=123, operation="create")
    info("Info message", user_email="user@example.com")
    error("Error message", error="Something went wrong")
"""


# Custom formatter that includes extra context
class ContextFormatter(logging.Formatter):
    def format(self, record):
        # Format the basic message
        formatted = super().format(record)

        # Always add extra context if present (dynamically, not hardcoded)
        standard_keys = set(
            [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "asctime",
            ]
        )
        context = {}
        for key, value in record.__dict__.items():
            if key not in standard_keys:
                context[key] = value
        if context:
            formatted += f" | Context: {json.dumps(context, default=str)}"
        return formatted


# Create a custom logger
logger = logging.getLogger("commco_app")
logger.setLevel(logging.DEBUG)


# Create handlers
def setup_logging():
    """Setup logging configuration with different levels and handlers"""

    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Get log levels from environment variables (default to INFO for app.log, DEBUG for debug.log)
    app_log_level = getattr(
        logging, os.getenv("APP_LOG_LEVEL", "INFO").upper(), logging.INFO
    )
    debug_log_level = getattr(
        logging, os.getenv("DEBUG_LOG_LEVEL", "DEBUG").upper(), logging.DEBUG
    )
    error_log_level = getattr(
        logging, os.getenv("ERROR_LOG_LEVEL", "ERROR").upper(), logging.ERROR
    )

    # File handler for all logs (INFO and above by default)
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(app_log_level)
    file_format = ContextFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Debug file handler (DEBUG and above)
    debug_handler = logging.FileHandler("logs/debug.log")
    debug_handler.setLevel(debug_log_level)
    debug_handler.setFormatter(file_format)

    # Error file handler
    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setLevel(error_log_level)
    error_handler.setFormatter(file_format)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)

    return logger


# Initialize logging
setup_logging()


# Convenience functions for different log levels
def debug(message, **kwargs):
    """Log a debug message"""
    logger.debug(message, extra=kwargs)


def info(message, **kwargs):
    """Log an info message"""
    logger.info(message, extra=kwargs)


def warning(message, **kwargs):
    """Log a warning message"""
    logger.warning(message, extra=kwargs)


def error(message, **kwargs):
    """Log an error message"""
    logger.error(message, extra=kwargs)


def critical(message, **kwargs):
    """Log a critical message"""
    logger.critical(message, extra=kwargs)


def exception(message, exc_info=True, **kwargs):
    """Log an exception with traceback"""
    logger.exception(message, extra=kwargs)


# Request logging decorator
def log_request(f):
    """Decorator to log incoming requests"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = getattr(g, "user", None)
        user_email = getattr(g.user, "email", "anonymous") if user_id else "anonymous"

        info(
            f"Request started",
            method=request.method,
            path=request.path,
            user_email=user_email,
            ip=request.remote_addr,
        )

        try:
            result = f(*args, **kwargs)
            info(
                f"Request completed successfully",
                method=request.method,
                path=request.path,
                user_email=user_email,
            )
            return result
        except Exception as e:
            error(
                f"Request failed",
                method=request.method,
                path=request.path,
                user_email=user_email,
                error=str(e),
            )
            raise

    return decorated_function


# Performance logging decorator
def log_performance(f):
    """Decorator to log function performance"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time

        start_time = time.time()

        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            info(
                f"Function {f.__name__} completed",
                execution_time=f"{execution_time:.4f}s",
                function=f.__name__,
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error(
                f"Function {f.__name__} failed",
                execution_time=f"{execution_time:.4f}s",
                function=f.__name__,
                error=str(e),
            )
            raise

    return decorated_function


# Database operation logging
def log_db_operation(operation, table, record_id=None, **kwargs):
    """Log database operations"""
    info(f"Database {operation}", table=table, record_id=record_id, **kwargs)


# Authentication logging
def log_auth_event(event, user_email=None, success=True, **kwargs):
    """Log authentication events"""
    level = info if success else warning
    level(f"Authentication {event}", user_email=user_email, success=success, **kwargs)


# API response logging
def log_api_response(status_code, endpoint, user_email=None, **kwargs):
    """Log API responses"""
    if status_code >= 400:
        level = error if status_code >= 500 else warning
    else:
        level = info

    level(
        f"API Response",
        status_code=status_code,
        endpoint=endpoint,
        user_email=user_email,
        **kwargs,
    )
