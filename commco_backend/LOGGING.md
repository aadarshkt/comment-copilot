# Logging System Documentation

This document explains how to use the comprehensive logging system implemented in the Flask application.

## Overview

The logging system provides different levels of logging (debug, info, warning, error, critical) with structured logging capabilities, automatic log rotation, and specialized logging for different types of operations.

## Log Levels

### 1. Debug Level

```python
from app.logging_utils import debug

debug("This is a debug message")
debug("User action", user_id=123, action="button_click")
```

- **Use for**: Detailed troubleshooting information
- **When**: During development or when you need to trace execution flow
- **Output**: Only shown when log level is set to DEBUG

### 2. Info Level

```python
from app.logging_utils import info

info("User logged in successfully")
info("Database operation completed", table="users", operation="INSERT")
```

- **Use for**: General application flow and successful operations
- **When**: Normal application events that are useful for monitoring
- **Output**: Shown for INFO level and above

### 3. Warning Level

```python
from app.logging_utils import warning

warning("Rate limit approaching")
warning("Invalid input received", input_value="invalid_email")
```

- **Use for**: Unexpected but non-critical issues
- **When**: Something went wrong but the application can continue
- **Output**: Shown for WARNING level and above

### 4. Error Level

```python
from app.logging_utils import error

error("Database connection failed")
error("API request failed", status_code=500, endpoint="/api/users")
```

- **Use for**: Errors that need attention
- **When**: Something went wrong and may affect functionality
- **Output**: Shown for ERROR level and above

### 5. Critical Level

```python
from app.logging_utils import critical

critical("Application cannot start - missing configuration")
critical("Database is down")
```

- **Use for**: Critical issues that may prevent the application from functioning
- **When**: Severe problems that require immediate attention
- **Output**: Shown for CRITICAL level only

### 6. Exception Level

```python
from app.logging_utils import exception

try:
    result = risky_operation()
except Exception as e:
    exception("Risky operation failed", error=str(e))
```

- **Use for**: Logging exceptions with full traceback
- **When**: Catching exceptions and want to log the full stack trace
- **Output**: Includes the full exception traceback

## Specialized Logging Functions

### Request Logging Decorator

```python
from app.logging_utils import log_request

@main_bp.route("/api/users")
@log_request
def get_users():
    # This function will automatically log:
    # - Request start with method, path, user, IP
    # - Request completion or failure
    return jsonify(users)
```

### Performance Logging Decorator

```python
from app.logging_utils import log_performance

@log_performance
def expensive_operation():
    # This function will log execution time
    time.sleep(1)
    return result
```

### Database Operation Logging

```python
from app.logging_utils import log_db_operation

# Log database operations
log_db_operation("INSERT", "users", record_id=123, email="user@example.com")
log_db_operation("UPDATE", "comments", record_id=456, status="approved")
log_db_operation("DELETE", "sessions", record_id=789)
```

### Authentication Event Logging

```python
from app.logging_utils import log_auth_event

# Log authentication events
log_auth_event("login_successful", user_email="user@example.com", success=True)
log_auth_event("login_failed", user_email="hacker@example.com", success=False, reason="invalid_password")
log_auth_event("logout", user_email="user@example.com")
```

### API Response Logging

```python
from app.logging_utils import log_api_response

# Log API responses with appropriate level based on status code
log_api_response(200, "/api/users", user_email="user@example.com")
log_api_response(404, "/api/users/999", user_email="user@example.com", error="User not found")
log_api_response(500, "/api/sync", user_email="user@example.com", error="Internal server error")
```

## Log Output

### Console Output

All logs are displayed in the console with the format:

```
2024-01-15 10:30:45,123 - commco_app - INFO - User logged in successfully
```

### File Output

Logs are also written to files in the `logs/` directory:

1. **`logs/app.log`** - All logs (INFO level and above)
2. **`logs/error.log`** - Only error and critical logs

### Log Format

```
2024-01-15 10:30:45,123 - commco_app - INFO - function_name:line_number - Message with context
```

## Configuration

### Environment Variables

You can configure logging behavior using environment variables:

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Set log file path
export LOG_FILE=logs/app.log

# Set maximum log file size (default: 10MB)
export LOG_MAX_BYTES=10485760

# Set number of backup files (default: 5)
export LOG_BACKUP_COUNT=5
```

### Log Rotation

Log files are automatically rotated when they reach the maximum size:

- `app.log` → `app.log.1` → `app.log.2` → etc.
- `error.log` → `error.log.1` → `error.log.2` → etc.

## Best Practices

### 1. Use Appropriate Log Levels

- **DEBUG**: Detailed troubleshooting
- **INFO**: Normal application flow
- **WARNING**: Unexpected but non-critical issues
- **ERROR**: Problems that need attention
- **CRITICAL**: Severe issues requiring immediate action

### 2. Include Context

```python
# Good
info("User logged in", user_id=123, email="user@example.com", ip="192.168.1.1")

# Bad
info("User logged in")
```

### 3. Use Structured Logging

```python
# Good - structured data
error("API request failed",
      endpoint="/api/users",
      status_code=500,
      user_id=123)

# Bad - unstructured message
error("API request to /api/users failed with 500 for user 123")
```

### 4. Don't Log Sensitive Information

```python
# Good
info("User authenticated", user_id=123)

# Bad
info("User authenticated", password="secret123", token="abc123")
```

### 5. Use Decorators for Common Patterns

```python
@log_request
@log_performance
def my_function():
    # Automatically logs request details and performance
    pass
```

## Testing the Logging System

Run the example script to see all logging levels in action:

```bash
cd commco_backend
python logging_example.py
```

This will generate sample logs and show you the output format.

## Integration with Flask

The logging system is automatically integrated into your Flask routes. When you use the `@log_request` decorator, it will:

1. Log the start of each request with method, path, user, and IP
2. Log the completion or failure of the request
3. Include user context when available

## Monitoring and Alerting

For production environments, consider:

1. **Log Aggregation**: Use tools like ELK Stack, Splunk, or Datadog
2. **Alerting**: Set up alerts for ERROR and CRITICAL level logs
3. **Metrics**: Track log volume and error rates
4. **Retention**: Configure appropriate log retention policies

## Troubleshooting

### Common Issues

1. **No logs appearing**: Check if the `logs/` directory exists and is writable
2. **Too many logs**: Adjust the log level or reduce debug logging
3. **Large log files**: Check log rotation settings
4. **Missing context**: Ensure you're passing relevant parameters to log functions

### Debug Mode

To enable debug logging, set the environment variable:

```bash
export LOG_LEVEL=DEBUG
```

This will show all log levels including debug messages.
