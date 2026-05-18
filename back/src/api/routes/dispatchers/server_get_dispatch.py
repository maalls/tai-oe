"""GET route dispatch for legacy API server."""

from src.api.action.routes import dispatch_action_routes
from src.api.csv.routes import dispatch_csv_routes
from src.api.email.handler import handle_google_oauth_callback_get


def dispatch_get_misc_routes(handler, parsed, qs) -> bool:
    """Dispatch misc GET routes and return True when handled."""
    if parsed.path.startswith('/api/google/oauth/callback'):
        handle_google_oauth_callback_get(handler, qs)
        return True

    if parsed.path.startswith('/api/prompt/'):
        handler._handle_prompt_get(parsed.path)
        return True

    return False


def dispatch_get_mail_routes(handler, parsed, qs) -> bool:
    """Legacy GET mail routes are disabled (served by FastAPI)."""
    _ = handler
    _ = parsed
    _ = qs
    return False


def dispatch_get_data_routes(handler, parsed, qs) -> bool:
    """Dispatch csv GET routes and return True when handled."""
    if dispatch_csv_routes(handler, "GET", parsed, qs):
        return True

    return False


def dispatch_get_action_download_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch action/download GET routes and return True when handled."""
    if dispatch_action_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    return False


def dispatch_get_request(handler, parsed, qs) -> bool:
    """Dispatch GET routes and return True when handled."""
    if dispatch_get_misc_routes(handler, parsed, qs):
        return True

    if dispatch_get_mail_routes(handler, parsed, qs):
        return True

    if dispatch_get_data_routes(handler, parsed, qs):
        return True

    request_handlers = handler.request_handlers
    if dispatch_get_action_download_routes(handler, parsed, qs, request_handlers):
        return True

    return False
