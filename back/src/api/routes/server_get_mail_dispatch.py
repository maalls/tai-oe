"""Mail/IMAP GET route dispatch for legacy API server."""

from src.api.email.routes import dispatch_email_routes


def dispatch_get_mail_routes(handler, parsed, qs) -> bool:
    """Dispatch gmail/imap/email attachment GET routes and return True when handled."""
    return dispatch_email_routes(handler, "GET", parsed, qs, handler.request_handlers)
