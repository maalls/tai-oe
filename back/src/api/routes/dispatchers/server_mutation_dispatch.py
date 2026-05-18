"""PATCH and PUT route dispatch for legacy API server."""

from types import SimpleNamespace

from src.api.action.routes import dispatch_action_routes


def dispatch_put_request(handler, parsed_path: str) -> bool:
    """Dispatch PUT routes and return True when handled."""
    parsed = SimpleNamespace(path=parsed_path)
    request_handlers = handler.request_handlers
    return dispatch_action_routes(handler, "PUT", parsed, {}, request_handlers)
