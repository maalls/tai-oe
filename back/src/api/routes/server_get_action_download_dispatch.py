"""Action and download GET route dispatch for legacy API server."""

from src.api.action.routes import dispatch_action_routes
from src.api.document.handler import handle_documents_download_get
from src.api.quote.handler import handle_quotes_download_get


def dispatch_get_action_download_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch action/download GET routes and return True when handled."""
    if dispatch_action_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    if parsed.path.startswith('/api/quotes/download/'):
        handle_quotes_download_get(handler, parsed.path, qs, request_handlers)
        return True

    if parsed.path.startswith('/api/documents/download/'):
        handle_documents_download_get(handler, parsed.path, qs, request_handlers)
        return True

    return False
