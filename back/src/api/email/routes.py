"""Domain router for email endpoints."""

import re
from typing import Any, Dict, Tuple

from src.api.email.handler import (
    handle_email_attachment_delete,
    handle_email_attachment_get,
    handle_email_auth_status_post,
    handle_email_delete,
    handle_email_extract_contact_post,
    handle_email_resync_post,
    handle_email_senders_high_risk_post,
    handle_email_senders_verified_post,
    handle_emails_classify_post,
    handle_gmail_authorize_get,
    handle_gmail_classify_unclassified_get,
    handle_gmail_message_get,
    handle_gmail_messages_get,
    handle_gmail_oauth_start_get,
    handle_gmail_profile_get,
    handle_gmail_revoke_get,
    handle_gmail_status_get,
    handle_imap_config_delete,
    handle_imap_config_get,
    handle_imap_config_post,
    handle_imap_status_get,
    handle_imap_test_post,
)


def classify_unclassified_route(
    handlers: Any,
    query: Dict[str, str],
    auth_user_id: str | None = None,
) -> Tuple[Dict[str, Any], int]:
    """Handle classify-unclassified request in a transport-agnostic way."""
    user_id = query.get("user_id") or auth_user_id
    if not user_id:
        return {"status": "error", "message": "Missing user_id"}, 400

    try:
        limit = int(query.get("limit", "200"))
    except Exception:
        limit = 200

    result = handlers.handle_classify_unclassified(
        user_id=user_id,
        limit=limit,
    )
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code


def dispatch_email_routes(handler, method: str, parsed, qs, _request_handlers) -> bool:
    """Dispatch email routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path == '/api/gmail/oauth/start':
            handle_gmail_oauth_start_get(handler, qs)
            return True

        if path == '/api/gmail/authorize':
            handle_gmail_authorize_get(handler, qs)
            return True

        if path == '/api/gmail/status':
            handle_gmail_status_get(handler, qs)
            return True

        if path == '/api/gmail/revoke':
            handle_gmail_revoke_get(handler, qs)
            return True

        if path == '/api/gmail/profile':
            handle_gmail_profile_get(handler, qs)
            return True

        if path == '/api/imap/status':
            handle_imap_status_get(handler)
            return True

        if path == '/api/imap/config':
            handle_imap_config_get(handler)
            return True

        if path == '/api/gmail/messages':
            handle_gmail_messages_get(handler, qs)
            return True

        if path == '/api/gmail/classify-unclassified':
            handle_gmail_classify_unclassified_get(handler, qs)
            return True

        if path.startswith('/api/gmail/message/'):
            handle_gmail_message_get(handler, path)
            return True

        if path.startswith('/api/email-attachment/'):
            handle_email_attachment_get(handler, path)
            return True

        return False

    if method == "POST":
        if path.startswith('/api/emails/classify/'):
            handle_emails_classify_post(handler, path)
            return True

        if path == '/api/email/extract-contact':
            handle_email_extract_contact_post(handler)
            return True

        if path.startswith('/api/email/auth/'):
            handle_email_auth_status_post(handler, path)
            return True

        if path.startswith('/api/email/') and path.endswith('/resync'):
            handle_email_resync_post(handler, path)
            return True

        if path == '/api/email/senders/high-risk':
            handle_email_senders_high_risk_post(handler)
            return True

        if path == '/api/email/senders/verified':
            handle_email_senders_verified_post(handler)
            return True

        if path == '/api/imap/config':
            handle_imap_config_post(handler)
            return True

        if path == '/api/imap/test':
            handle_imap_test_post(handler)
            return True

        return False

    if method == "DELETE":
        attachment_delete_match = re.match(r"^/api/email-attachment/([^/]+)$", path)
        if attachment_delete_match:
            handle_email_attachment_delete(handler, attachment_delete_match)
            return True

        email_delete_match = re.match(r"^/api/email/([^/]+)$", path)
        if email_delete_match:
            handle_email_delete(handler, email_delete_match)
            return True

        if path == '/api/imap/config':
            handle_imap_config_delete(handler)
            return True

        return False

    return False