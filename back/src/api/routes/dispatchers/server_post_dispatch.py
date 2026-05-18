"""POST route dispatch for legacy API server."""

from src.api.invoice.routes import dispatch_invoice_routes


def dispatch_post_business_routes(handler, parsed) -> bool:
    """Dispatch invoice POST routes and return True when handled."""
    request_handlers = handler.request_handlers

    if dispatch_invoice_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    return False


def dispatch_post_request(handler, parsed) -> bool:
    """Dispatch POST routes and return True when handled."""
    if dispatch_post_business_routes(handler, parsed):
        return True

    return False
