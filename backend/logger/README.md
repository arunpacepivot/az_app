# Error Logging System

A centralized, asynchronous error logging system for capturing and storing errors from all parts of the application.

## Features

- **Automatic Error Capturing**: Middleware automatically captures unhandled exceptions in API views
- **Asynchronous Logging**: Error logging happens in background threads to avoid impacting performance
- **Component Detection**: Automatically detects which component/module an error came from
- **Comprehensive Data**: Captures error message, traceback, request details, and more
- **API Request Logging**: Logs API requests and responses for network debugging
- **API Access**: View and filter errors through a REST API
- **Admin Interface**: Browse errors through the Django admin site

## How It Works

This system captures errors in three ways:

1. **Middleware** - All unhandled exceptions in API views are automatically captured
2. **Explicit Logging** - Code can explicitly log errors using the `log()` function
3. **Network Monitoring** - HTTP requests can be logged using `log_request()` or automatic patching

The system automatically detects which component an error came from based on the URL pattern or module name.

## Usage

### Automatic Error Logging (No Code Changes Required)

The middleware will automatically log all unhandled exceptions in views with no code changes required.

### Simple Logging

```python
from logger import log

# Basic error logging
log("Failed to process file")

# With additional information
log(
    message="Invalid file format", 
    level="WARNING", 
    component="file_processor", 
    metadata={"file": "data.xlsx", "format": "csv"}
)

# Logging an exception with traceback
try:
    process_file(file_path)
except Exception as e:
    log("Error processing file", exc_info=e, metadata={"file": file_path})
```

### API Request Logging

```python
from logger import log_request

# Log a completed request
response = requests.get("https://api.example.com/data")
log_request(
    url="https://api.example.com/data",
    method="GET",
    status_code=response.status_code,
    response_data=response.json(),
    duration_ms=250
)

# Log a failed request
try:
    response = requests.post("https://api.example.com/data", json=data)
    response.raise_for_status()
except Exception as e:
    log_request(
        url="https://api.example.com/data",
        method="POST",
        request_data=data,
        error=e
    )
```

### Automatic Request Monitoring

You can automatically log all requests made with the `requests` library:

```python
from logger import RequestsMonitor

# Call this once at application startup
RequestsMonitor.patch()

# Now all requests made with the requests library will be automatically logged
response = requests.get("https://api.example.com/data")
# This request is automatically logged - no need to call log_request()
```

### Error Logging Decorator

```python
from logger import auto_log_errors

# Automatically log any errors in this function
@auto_log_errors()
def process_file(file_path):
    # Any uncaught exception will be automatically logged
    with open(file_path, 'r') as f:
        return process_data(f.read())

# You can specify the source and component
@auto_log_errors(source='SP', component='file_processor')
def another_function():
    # ...
```

## Log Parameters

The `log()` function accepts the following parameters:

- `message`: The log message
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `source`: Source component (auto-detected if not provided)
- `component`: Component name (auto-detected if not provided)
- `exc_info`: Exception info (True for current exception, or pass an exception instance)
- `metadata`: Dictionary with additional contextual information

## Viewing Errors

Errors can be viewed in two ways:

1. **Django Admin**: Go to `/admin/logger/errorlog/` to browse all errors
2. **API**: Use the REST API endpoints:
   - GET `/api/v1/logger/logs/` - List all errors (with pagination)
   - GET `/api/v1/logger/stats/` - Get error statistics

## API Endpoints

### GET /api/v1/logger/logs/

Lists all error logs with pagination, filtering, and searching.

Query parameters:
- `level`: Filter by error level
- `source`: Filter by source component
- `component`: Filter by specific component
- `search`: Search in message and component
- `ordering`: Order results (e.g. `-timestamp` for newest first)
- `page`: Page number
- `page_size`: Results per page

### GET /api/v1/logger/stats/

Get statistics about error logs:
- Count by level
- Count by source
- Count by date (last 7 days)
- Total count 