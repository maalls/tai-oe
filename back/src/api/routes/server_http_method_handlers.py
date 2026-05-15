"""HTTP method handlers for legacy API server."""

import urllib.parse

from src.api.routes.server_head_dispatch import dispatch_head_request


def handle_options_method(handler):
    """Handle OPTIONS method."""
    handler.send_response(200)
    handler.end_headers()
    return None


def handle_head_method(handler):
    """Handle HEAD method."""
    try:
        parsed = urllib.parse.urlparse(handler.path)

        if dispatch_head_request(handler, parsed.path):
            return None

        return handler._send_error(404, "Not found")
    except Exception as e:
        return handler._send_error(500, f"Internal server error 2: {e}")
