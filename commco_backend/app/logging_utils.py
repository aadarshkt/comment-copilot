import logging
import os
import json
from functools import wraps
from flask import request, g
import traceback


# Custom formatter that includes extra context
class ContextFormatter(logging.Formatter):
    def format(self, record):
        # Format the basic message
        formatted = super().format(record)

        # Add extra context if present
        if (
            hasattr(record, "user_id")
            or hasattr(record, "count")
            or hasattr(record, "email")
            or hasattr(record, "ip")
            or hasattr(record, "method")
            or hasattr(record, "path")
            or hasattr(record, "error")
            or hasattr(record, "status_code")
            or hasattr(record, "endpoint")
            or hasattr(record, "execution_time")
            or hasattr(record, "function")
            or hasattr(record, "table")
            or hasattr(record, "record_id")
            or hasattr(record, "operation")
            or hasattr(record, "success")
            or hasattr(record, "channel_id")
            or hasattr(record, "youtube_channel_id")
            or hasattr(record, "category")
            or hasattr(record, "google_id")
            or hasattr(record, "file_path")
            or hasattr(record, "session_state")
            or hasattr(record, "request_state")
            or hasattr(record, "status_code")
            or hasattr(record, "response_text")
            or hasattr(record, "dividend")
            or hasattr(record, "divisor")
            or hasattr(record, "user_level")
            or hasattr(record, "request_count")
            or hasattr(record, "limit")
            or hasattr(record, "database")
            or hasattr(record, "retry_count")
            or hasattr(record, "input_value")
            or hasattr(record, "valid_categories")
            or hasattr(record, "reason")
        ):
            context = {}
            for key, value in record.__dict__.items():
                if key not in [
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
                ]:
                    if key not in [
                        "asctime",
                        "name",
                        "levelname",
                        "funcName",
                        "lineno",
                    ]:
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

    # File handler for all logs
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(logging.INFO)
    file_format = ContextFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Error file handler
    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)

    # Add handlers to logger (file handlers only)
    logger.addHandler(file_handler)
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
