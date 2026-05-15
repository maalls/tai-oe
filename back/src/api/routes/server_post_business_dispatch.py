"""Business POST route dispatch for legacy API server."""

from src.api.document.routes import dispatch_document_routes
from src.api.invoice.routes import dispatch_invoice_routes
from src.api.opportunity.routes import dispatch_opportunity_routes
from src.api.quote.routes import dispatch_quote_routes


def dispatch_post_business_routes(handler, parsed) -> bool:
    """Dispatch opportunity/quote/invoice POST routes and return True when handled."""
    request_handlers = handler.request_handlers

    if dispatch_opportunity_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_document_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_quote_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_invoice_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    return False
