"""DELETE route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.action.routes import dispatch_action_routes
from src.api.document.routes import dispatch_document_routes
from src.api.email.routes import dispatch_email_routes
from src.api.opportunity.routes import dispatch_opportunity_routes
from src.api.quote.routes import dispatch_quote_routes


def dispatch_delete_request(handler, parsed_path: str) -> bool:
    """Dispatch DELETE routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers

    if dispatch_action_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    if dispatch_email_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    if dispatch_quote_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    if dispatch_opportunity_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    if dispatch_document_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    return False
