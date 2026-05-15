"""Compatibility facade for CSV GET route handlers."""

from src.api.csv.handler import (
    handle_csv_files_get,
    handle_csv_get,
    handle_csv_preview_get,
    handle_csv_query_get,
    handle_csv_search_get,
    handle_csv_sources_get,
)

__all__ = [
    "handle_csv_get",
    "handle_csv_files_get",
    "handle_csv_preview_get",
    "handle_csv_sources_get",
    "handle_csv_query_get",
    "handle_csv_search_get",
]
