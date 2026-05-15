"""Utility POST handlers for legacy API server."""


def handle_products_post(handler):
    """Handle /api/products POST endpoint."""
    payload = handler._read_json(default={})
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_product(payload)
    return handler.json(result, 201)
