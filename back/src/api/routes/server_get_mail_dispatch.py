"""Mail/IMAP GET route dispatch for legacy API server."""

from src.api.email.handler import (
    handle_email_attachment_get,
    handle_gmail_authorize_get,
    handle_gmail_oauth_start_get,
    handle_gmail_profile_get,
    handle_gmail_revoke_get,
    handle_gmail_status_get,
    handle_imap_config_get,
    handle_imap_status_get,
    handle_gmail_messages_get,
    handle_gmail_classify_unclassified_get,
    handle_gmail_message_get,
)


def dispatch_get_mail_routes(handler, parsed, qs) -> bool:
    """Dispatch gmail/imap/email attachment GET routes and return True when handled."""
    if parsed.path == '/api/gmail/oauth/start':
        handle_gmail_oauth_start_get(handler, qs)
        return True
    if parsed.path == '/api/gmail/authorize':
        handle_gmail_authorize_get(handler, qs)
        return True
    if parsed.path == '/api/gmail/status':
        handle_gmail_status_get(handler, qs)
        return True
    if parsed.path == '/api/gmail/revoke':
        handle_gmail_revoke_get(handler, qs)
        return True
    if parsed.path == '/api/gmail/profile':
        handle_gmail_profile_get(handler, qs)
        return True
    if parsed.path == '/api/imap/status':
        handle_imap_status_get(handler)
        return True
    if parsed.path == '/api/imap/config':
        handle_imap_config_get(handler)
        return True
    if parsed.path == '/api/gmail/messages':
        handle_gmail_messages_get(handler, qs)
        return True
    if parsed.path == '/api/gmail/classify-unclassified':
        handle_gmail_classify_unclassified_get(handler, qs)
        return True
    if parsed.path.startswith('/api/gmail/message/'):
        handle_gmail_message_get(handler, parsed.path)
        return True
    if parsed.path.startswith('/api/email-attachment/'):
        handle_email_attachment_get(handler, parsed.path)
        return True

    return False
