"""Mail/IMAP GET route dispatch for legacy API server."""


def dispatch_get_mail_routes(handler, parsed, qs) -> bool:
    """Dispatch gmail/imap/email attachment GET routes and return True when handled."""
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

    return False
