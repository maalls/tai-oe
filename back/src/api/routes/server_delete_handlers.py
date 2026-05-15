"""Compatibility facade for legacy DELETE route handlers.

Implementation is now organized in domain handler modules under src.api.*.handler.
This module preserves stable imports for server wiring and tests.
"""

from src.api.action.handler import handle_action_delete
from src.api.document.handler import (
    handle_document_delete,
    handle_quote_delete,
)
from src.api.email.handler import (
    handle_email_attachment_delete,
    handle_email_delete,
    handle_imap_config_delete,
)
from src.api.opportunity.handler import handle_opportunity_delete

__all__ = [
    "handle_imap_config_delete",
    "handle_action_delete",
    "handle_email_delete",
    "handle_email_attachment_delete",
    "handle_document_delete",
    "handle_quote_delete",
    "handle_opportunity_delete",
]
