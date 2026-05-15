"""Basic Gmail/IMAP GET handlers for legacy API server."""


def handle_gmail_status_get(handler, qs):
    """Handle /api/gmail/status GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_status(user_id=user_id)
    return handler.json(result)


def handle_gmail_authorize_get(handler, qs):
    """Handle /api/gmail/authorize GET endpoint."""
    request_handlers = handler.get_request_handlers()
    redirect_url = handler._get_qs_value(qs, 'redirect_url')
    result = request_handlers.handle_gmail_authorize(redirect_url)
    return handler.json(result)


def handle_gmail_oauth_start_get(handler, qs):
    """Handle /api/gmail/oauth/start GET endpoint."""
    request_handlers = handler.get_request_handlers()
    redirect_url = handler._get_qs_value(qs, 'redirect_url')
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_oauth_start(redirect_url, user_id=user_id)
    return handler.json(result)


def handle_gmail_revoke_get(handler, qs):
    """Handle /api/gmail/revoke GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_revoke(user_id=user_id)
    return handler.json(result)


def handle_gmail_profile_get(handler, qs):
    """Handle /api/gmail/profile GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = handler._get_qs_value(qs, 'user_id')
    result = request_handlers.handle_gmail_profile(user_id=user_id)
    return handler.json(result)


def handle_imap_status_get(handler):
    """Handle /api/imap/status GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_status(user_id=user_id)
    return handler.json(result)


def handle_imap_config_get(handler):
    """Handle /api/imap/config GET endpoint."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_config(user_id=user_id)
    return handler.json(result)
