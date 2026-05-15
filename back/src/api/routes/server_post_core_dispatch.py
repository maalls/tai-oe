"""Core POST route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.file.routes import dispatch_file_routes
from src.api.product.routes import dispatch_product_routes


def dispatch_post_core_routes(handler, parsed_path: str) -> bool:
    """Dispatch core POST routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers

    if dispatch_product_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_file_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    return False
