"""Domain POST route dispatch for legacy API server."""

from src.api.document.routes import dispatch_document_routes
from src.api.email.routes import dispatch_email_routes
from src.api.entity.routes import dispatch_entity_routes
from src.api.opportunity.routes import dispatch_opportunity_routes
from src.api.rfq.routes import dispatch_rfq_routes


def dispatch_post_domain_routes(handler, parsed) -> bool:
    """Dispatch domain POST routes and return True when handled."""
    request_handlers = handler.request_handlers

    if dispatch_email_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_entity_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_rfq_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_opportunity_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_document_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    return False
