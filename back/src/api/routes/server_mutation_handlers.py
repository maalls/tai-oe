"""PUT/PATCH mutation handlers for legacy API server."""


def handle_action_update_put(handler, update_action_match):
    """Handle PUT /api/actions/{id}."""
    data = handler._read_json_or_error()
    if data is None:
        return None

    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    action_id = update_action_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_update_action(action_id, data, user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)
