"""Request body parsing helpers for legacy API server."""

import json


def read_body(handler) -> bytes:
    """Read raw request body based on Content-Length."""
    content_length = int(handler.headers.get('Content-Length', 0))
    return handler.rfile.read(content_length)


def read_json(handler, default=None):
    """Read and decode JSON payload with default fallback."""
    body = handler._read_body()
    try:
        return json.loads(body.decode('utf-8') or '{}')
    except Exception:
        return {} if default is None else default


def read_json_or_error(handler, error_payload=None, status_code=400):
    """Read JSON payload and emit formatted error response on invalid JSON."""
    body = handler._read_body()
    try:
        return json.loads(body.decode('utf-8') or '{}')
    except Exception:
        handler.json(error_payload or {"status": "error", "message": "Invalid JSON"}, status_code)
        return None
