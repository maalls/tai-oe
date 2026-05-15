"""Compatibility facade for streaming GET route handlers."""

from src.api.csv.handler import (
    handle_csv_download,
    handle_raw_stream,
    handle_source_stream,
)

__all__ = [
    "handle_raw_stream",
    "handle_csv_download",
    "handle_source_stream",
]
