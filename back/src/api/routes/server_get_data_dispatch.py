"""Data GET route dispatch for legacy API server."""

from src.api.csv.routes import dispatch_csv_routes
from src.api.opportunity.handler import handle_opportunities_search_get
from src.api.quote.handler import handle_quotes_list_get


def dispatch_get_data_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch csv/quotes/opportunity search GET routes and return True when handled."""
    if dispatch_csv_routes(handler, "GET", parsed, qs):
        return True

    if parsed.path == '/api/quotes/list':
        handle_quotes_list_get(handler, request_handlers)
        return True

    if parsed.path == '/api/opportunities/search':
        handle_opportunities_search_get(handler, qs, request_handlers)
        return True

    return False
