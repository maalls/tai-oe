"""Data GET route dispatch for legacy API server."""

from src.api.csv.routes import dispatch_csv_routes
from src.api.opportunity.routes import dispatch_opportunity_routes
from src.api.quote.routes import dispatch_quote_routes


def dispatch_get_data_routes(handler, parsed, qs, request_handlers) -> bool:
    """Dispatch csv/quotes/opportunity search GET routes and return True when handled."""
    if dispatch_csv_routes(handler, "GET", parsed, qs):
        return True

    if dispatch_quote_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    if dispatch_opportunity_routes(handler, "GET", parsed, qs, request_handlers):
        return True

    return False
