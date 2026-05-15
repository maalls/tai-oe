"""Compatibility facade for detailed mail GET route handlers."""

from src.api.email.handler import (
    handle_email_attachment_get,
    handle_gmail_classify_unclassified_get,
    handle_gmail_message_get,
    handle_gmail_messages_get,
)

__all__ = [
    "handle_gmail_messages_get",
    "handle_gmail_classify_unclassified_get",
    "handle_gmail_message_get",
    "handle_email_attachment_get",
]
