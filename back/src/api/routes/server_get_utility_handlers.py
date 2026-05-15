"""Compatibility facade for utility GET route handlers."""

from src.api.action.handler import (
    handle_action_get,
    handle_action_logs_get,
    handle_opportunity_actions_list_get,
)
from src.api.document.handler import handle_documents_download_get
from src.api.opportunity.handler import handle_opportunities_search_get
from src.api.quote.handler import (
    handle_quotes_download_get,
    handle_quotes_list_get,
)

__all__ = [
    "handle_opportunities_search_get",
    "handle_opportunity_actions_list_get",
    "handle_action_get",
    "handle_action_logs_get",
    "handle_quotes_download_get",
    "handle_documents_download_get",
    "handle_quotes_list_get",
]
