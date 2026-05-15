"""GET route dispatch for legacy API server."""

import re

from src.api.routes.server_get_misc_dispatch import dispatch_get_misc_routes
from src.api.routes.server_get_auth_dispatch import dispatch_get_auth_routes


def dispatch_get_request(handler, parsed, qs) -> bool:
    """Dispatch GET routes and return True when handled."""
    if handler._handle_ddd_get_routes(parsed, qs):
        return True

    if dispatch_get_misc_routes(handler, parsed, qs):
        return True

    if dispatch_get_auth_routes(handler, parsed, qs):
        return True

    if parsed.path == '/api/gmail/oauth/start':
        handler._handle_gmail_oauth_start_get(qs)
        return True
    if parsed.path == '/api/gmail/authorize':
        handler._handle_gmail_authorize_get(qs)
        return True
    if parsed.path == '/api/gmail/status':
        handler._handle_gmail_status_get(qs)
        return True
    if parsed.path == '/api/gmail/revoke':
        handler._handle_gmail_revoke_get(qs)
        return True
    if parsed.path == '/api/gmail/profile':
        handler._handle_gmail_profile_get(qs)
        return True
    if parsed.path == '/api/imap/status':
        handler._handle_imap_status_get()
        return True
    if parsed.path == '/api/imap/config':
        handler._handle_imap_config_get()
        return True
    if parsed.path == '/api/gmail/messages':
        handler._handle_gmail_messages_get(qs)
        return True
    if parsed.path == '/api/gmail/classify-unclassified':
        handler._handle_gmail_classify_unclassified_get(qs)
        return True
    if parsed.path.startswith('/api/gmail/message/'):
        handler._handle_gmail_message_get(parsed.path)
        return True
    if parsed.path.startswith('/api/email-attachment/'):
        handler._handle_email_attachment_get(parsed.path)
        return True

    if parsed.path.startswith('/api/csv'):
        handler._handle_csv_get(parsed.path, qs)
        return True

    request_handlers = handler.get_request_handlers()
    if parsed.path == '/api/quotes/list':
        handler._handle_quotes_list_get(request_handlers)
        return True
    if parsed.path == '/api/opportunities/search':
        handler._handle_opportunities_search_get(qs, request_handlers)
        return True

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
