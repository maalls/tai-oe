"""Action and download GET route dispatch for legacy API server."""

from src.api.action.routes import dispatch_action_routes
from src.api.document.routes import dispatch_document_routes
from src.api.quote.routes import dispatch_quote_routes


def dispatch_get_action_download_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch action/download GET routes and return True when handled."""
    if dispatch_action_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    if dispatch_quote_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    if dispatch_document_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    return False
