"""Action and download GET route dispatch for legacy API server."""

import re

from src.api.action.handler import handle_action_get, handle_action_logs_get, handle_opportunity_actions_list_get
from src.api.document.handler import handle_documents_download_get
from src.api.quote.handler import handle_quotes_download_get


def dispatch_get_action_download_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch action/download GET routes and return True when handled."""
    list_actions_match = re.match(r"^/api/opportunities/([^/]+)/actions$", parsed.path)
    if list_actions_match:
        handle_opportunity_actions_list_get(handler, list_actions_match, request_handlers)
        return True

    get_action_match = re.match(r"^/api/actions/([^/]+)$", parsed.path)
    if get_action_match:
        handle_action_get(handler, get_action_match, request_handlers)
        return True

    get_action_logs_match = re.match(r"^/api/actions/([^/]+)/logs$", parsed.path)
    if get_action_logs_match:
        handle_action_logs_get(handler, get_action_logs_match, qs, request_handlers)
        return True

    if parsed.path.startswith('/api/quotes/download/'):
        handle_quotes_download_get(handler, parsed.path, qs, request_handlers)
        return True

    if parsed.path.startswith('/api/documents/download/'):
        handle_documents_download_get(handler, parsed.path, qs, request_handlers)
        return True

    return False
