"""Action and download GET route dispatch for legacy API server."""

import re


def dispatch_get_action_download_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch action/download GET routes and return True when handled."""
    list_actions_match = re.match(r"^/api/opportunities/([^/]+)/actions$", parsed.path)
    if list_actions_match:
        handler._handle_opportunity_actions_list_get(list_actions_match, request_handlers)
        return True

    get_action_match = re.match(r"^/api/actions/([^/]+)$", parsed.path)
    if get_action_match:
        handler._handle_action_get(get_action_match, request_handlers)
        return True

    get_action_logs_match = re.match(r"^/api/actions/([^/]+)/logs$", parsed.path)
    if get_action_logs_match:
        handler._handle_action_logs_get(get_action_logs_match, qs, request_handlers)
        return True

    if parsed.path.startswith('/api/quotes/download/'):
        handler._handle_quotes_download_get(parsed.path, qs, request_handlers)
        return True

    if parsed.path.startswith('/api/documents/download/'):
        handler._handle_documents_download_get(parsed.path, qs, request_handlers)
        return True

    return False
