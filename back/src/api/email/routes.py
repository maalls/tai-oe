"""Domain router for email endpoints."""

import re

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
)


def dispatch_email_routes(handler, method: str, parsed, qs, _request_handlers) -> bool:
    """Dispatch email routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
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

        return False

    return False