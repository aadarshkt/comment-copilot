#!/usr/bin/env python3
"""
Example script demonstrating how to use the logging system in the Flask application.
This shows all the different log levels and utility functions available.
"""

from app.logging_utils import (
    debug,
    info,
    warning,
    error,
    critical,
    exception,
    log_performance,
    log_db_operation,
    log_auth_event,
    log_api_response,
)


def example_basic_logging():
    """Demonstrate basic logging levels"""
    print("=== Basic Logging Levels ===")

    debug("This is a debug message - useful for detailed troubleshooting")
    info("This is an info message - general application flow")
    warning("This is a warning message - something unexpected but not critical")
    error("This is an error message - something went wrong")
    critical("This is a critical message - application may not function properly")


def example_logging_with_context():
    """Demonstrate logging with additional context"""
    print("\n=== Logging with Context ===")

    user_id = 123
    email = "user@example.com"

    info(
        "User logged in successfully",
        user_id=user_id,
        email=email,
        ip_address="192.168.1.1",
    )

    warning("Rate limit approaching", user_id=user_id, requests_this_hour=95, limit=100)

    error(
        "Database connection failed",
        user_id=user_id,
        database="postgresql",
        retry_count=3,
    )


def example_exception_logging():
    """Demonstrate exception logging"""
    print("\n=== Exception Logging ===")

    try:
        # Simulate an error
        result = 10 / 0
    except Exception as e:
        exception(
            "Division by zero error occurred", dividend=10, divisor=0, error=str(e)
        )


def example_performance_logging():
    """Demonstrate performance logging decorator"""
    print("\n=== Performance Logging ===")

    @log_performance
    def slow_function():
        import time

        time.sleep(0.1)  # Simulate work
        return "completed"

    result = slow_function()
    print(f"Function result: {result}")


def example_database_logging():
    """Demonstrate database operation logging"""
    print("\n=== Database Operation Logging ===")

    log_db_operation("INSERT", "users", record_id=456, email="newuser@example.com")

    log_db_operation("UPDATE", "comments", record_id=789, status="approved")

    log_db_operation("DELETE", "sessions", record_id=123)


def example_auth_logging():
    """Demonstrate authentication event logging"""
    print("\n=== Authentication Event Logging ===")

    log_auth_event("login_attempt", user_email="user@example.com", success=True)
    log_auth_event(
        "login_attempt",
        user_email="hacker@example.com",
        success=False,
        reason="invalid_password",
    )
    log_auth_event("password_reset", user_email="user@example.com", success=True)


def example_api_logging():
    """Demonstrate API response logging"""
    print("\n=== API Response Logging ===")

    log_api_response(200, "/api/user/me", user_email="user@example.com")
    log_api_response(
        404,
        "/api/comments/999",
        user_email="user@example.com",
        error="Comment not found",
    )
    log_api_response(
        500, "/api/sync", user_email="user@example.com", error="Internal server error"
    )


def example_conditional_logging():
    """Demonstrate conditional logging based on conditions"""
    print("\n=== Conditional Logging ===")

    user_level = "premium"
    request_count = 150

    if request_count > 100:
        warning(
            "High request volume detected",
            user_level=user_level,
            request_count=request_count,
        )

    if user_level == "premium":
        info("Premium user accessing advanced features", user_level=user_level)
    else:
        debug("Standard user accessing basic features", user_level=user_level)


if __name__ == "__main__":
    print("Flask Application Logging Examples")
    print("=" * 50)

    example_basic_logging()
    example_logging_with_context()
    example_exception_logging()
    example_performance_logging()
    example_database_logging()
    example_auth_logging()
    example_api_logging()
    example_conditional_logging()

    print("\n" + "=" * 50)
    print("Check the logs/ directory for the generated log files:")
    print("- logs/app.log (all logs)")
    print("- logs/error.log (error logs only)")
    print("Console output also shows all logs in real-time.")
