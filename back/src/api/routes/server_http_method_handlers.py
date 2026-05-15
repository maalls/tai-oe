"""HTTP method handlers for legacy API server."""


def handle_options_method(handler):
    """Handle OPTIONS method."""
    handler.send_response(200)
    handler.end_headers()
    return None
