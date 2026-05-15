"""Compatibility facade for basic mail GET route handlers."""

from src.api.email.handler import (
    handle_gmail_authorize_get,
    handle_gmail_oauth_start_get,
    handle_gmail_profile_get,
    handle_gmail_revoke_get,
    handle_gmail_status_get,
    handle_imap_config_get,
    handle_imap_status_get,
)

__all__ = [
    "handle_gmail_status_get",
    "handle_gmail_authorize_get",
    "handle_gmail_oauth_start_get",
    "handle_gmail_revoke_get",
    "handle_gmail_profile_get",
    "handle_imap_status_get",
    "handle_imap_config_get",
]
