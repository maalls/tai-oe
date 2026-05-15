"""Miscellaneous GET handlers for legacy API server."""


def handle_products_get(handler, qs):
    """Handle /api/products GET endpoint."""
    request_handlers = handler.get_request_handlers()
    return handler.json(request_handlers.handle_list_products(qs))
