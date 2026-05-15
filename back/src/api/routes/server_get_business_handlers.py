"""Business/action/download GET handlers for legacy API server."""

import urllib.parse


def handle_opportunities_search_get(handler, qs, request_handlers):
    """Handle /api/opportunities/search GET endpoint."""
    source_reference_id = qs.get('source_reference_id', [None])[0]
    name = qs.get('name', [None])[0]

    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    result = request_handlers.handle_search_opportunities(
        user_id=user_id,
        source_reference_id=source_reference_id,
        name=name,
    )
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_opportunity_actions_list_get(handler, list_actions_match, request_handlers):
    """Handle /api/opportunities/<id>/actions GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    opportunity_id = list_actions_match.group(1)
    result = request_handlers.handle_list_actions(opportunity_id, user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_action_get(handler, get_action_match, request_handlers):
    """Handle /api/actions/<id> GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    action_id = get_action_match.group(1)
    result = request_handlers.handle_get_action(action_id, user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_action_logs_get(handler, get_action_logs_match, qs, request_handlers):
    """Handle /api/actions/<id>/logs GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    action_id = get_action_logs_match.group(1)
    limit = handler._get_qs_int(qs, 'limit', 50)
    result = request_handlers.handle_get_action_logs(action_id, limit, user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_quotes_download_get(handler, parsed_path: str, qs, request_handlers):
    """Handle /api/quotes/download/<filename> GET endpoint."""
    filename = parsed_path.split('/api/quotes/download/')[-1]
    return handler._handle_quote_download(filename, request_handlers, qs)


def handle_documents_download_get(handler, parsed_path: str, qs, request_handlers):
    """Handle /api/documents/download/<filename> GET endpoint."""
    filename = parsed_path.split('/api/documents/download/')[-1]
    filename = urllib.parse.unquote(filename)
    return handler._handle_document_download(filename, request_handlers, qs)


def handle_quotes_list_get(handler, request_handlers):
    """Handle /api/quotes/list GET endpoint."""
    return handler.json(request_handlers.handle_list_quotes())
