"""Request body parsing helpers for legacy API server."""

import json


def read_body(handler) -> bytes:
    """Read raw request body based on Content-Length."""
    content_length = int(handler.headers.get('Content-Length', 0))
    return handler.rfile.read(content_length)
