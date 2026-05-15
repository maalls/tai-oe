"""POST route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.action.routes import dispatch_action_routes
from src.api.auth.routes import dispatch_auth_routes
from src.api.csv.routes import dispatch_csv_routes
from src.api.document.routes import dispatch_document_routes
from src.api.email.routes import dispatch_email_routes
from src.api.entity.routes import dispatch_entity_routes
from src.api.file.routes import dispatch_file_routes
from src.api.invoice.routes import dispatch_invoice_routes
from src.api.opportunity.routes import dispatch_opportunity_routes
from src.api.product.routes import dispatch_product_routes
from src.api.quote.routes import dispatch_quote_routes
from src.api.rfq.routes import dispatch_rfq_routes


def dispatch_post_core_routes(handler, parsed_path: str) -> bool:
    """Dispatch core POST routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers

    if dispatch_product_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_file_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    return False


def dispatch_post_auth_routes(handler, parsed_path: str) -> bool:
    """Dispatch auth POST routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    return dispatch_auth_routes(handler, "POST", parsed, {})


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


def dispatch_action_post_routes(handler, parsed_path: str) -> bool:
    """Dispatch action-specific POST regex routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers
    return dispatch_action_routes(handler, "POST", parsed, {}, request_handlers)


def dispatch_post_legacy_and_action_routes(handler, parsed_path: str) -> bool:
    """Dispatch remaining legacy/action POST routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers

    if dispatch_csv_routes(handler, "POST", parsed, {}):
        return True

    if dispatch_rfq_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_quote_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_action_post_routes(handler, parsed_path):
        return True

    return False


def dispatch_post_request(handler, parsed) -> bool:
    """Dispatch POST routes and return True when handled."""
    if handler._handle_ddd_post_routes(parsed):
        return True

    if dispatch_post_core_routes(handler, parsed.path):
        return True

    if dispatch_post_auth_routes(handler, parsed.path):
        return True

    if dispatch_post_domain_routes(handler, parsed):
        return True

    if dispatch_post_business_routes(handler, parsed):
        return True

    if dispatch_post_legacy_and_action_routes(handler, parsed.path):
        return True

    return False
