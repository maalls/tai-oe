"""DELETE route dispatch for legacy API server."""

import re
from types import SimpleNamespace

from src.api.action.routes import dispatch_action_routes
from src.api.document.handler import handle_document_delete, handle_quote_delete
from src.api.email.routes import dispatch_email_routes
from src.api.opportunity.handler import handle_opportunity_delete


def dispatch_delete_request(handler, parsed_path: str) -> bool:
    """Dispatch DELETE routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers

    if dispatch_action_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    if dispatch_email_routes(handler, "DELETE", parsed, {}, request_handlers):
        return True

    quote_delete_match = re.match(r"^/api/quote/([^/]+)$", parsed.path)
    if quote_delete_match:
        handle_quote_delete(handler, quote_delete_match)
        return True

    opportunity_delete_match = re.match(r"^/api/opportunities/([^/]+)$", parsed.path)
    if opportunity_delete_match:
        handle_opportunity_delete(handler, opportunity_delete_match)
        return True

    document_delete_match = re.match(r"^/api/document/([^/]+)$", parsed.path)
    if document_delete_match:
        handle_document_delete(handler, document_delete_match)
        return True

    return False
