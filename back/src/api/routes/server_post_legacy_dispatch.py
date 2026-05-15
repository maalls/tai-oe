"""Legacy and action POST route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.action.routes import dispatch_action_routes
from src.api.csv.routes import dispatch_csv_routes
from src.api.quote.routes import dispatch_quote_routes
from src.api.rfq.handler import handle_rfp_post


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

    if parsed_path == '/api/rfp':
        handle_rfp_post(handler)
        return True

    if dispatch_quote_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_action_post_routes(handler, parsed_path):
        return True

    return False
