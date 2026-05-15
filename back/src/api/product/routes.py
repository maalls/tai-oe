"""Domain router for product endpoints."""

from src.api.product.handler import handle_products_get, handle_products_post


def dispatch_product_routes(handler, method: str, parsed, qs, _request_handlers) -> bool:
    """Dispatch product routes across HTTP methods and return True when handled."""
    if parsed.path != '/api/products':
        return False

    if method == "GET":
        handle_products_get(handler, qs)
        return True

    if method == "POST":
        handle_products_post(handler)
        return True

    return False
