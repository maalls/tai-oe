"""Database query repository boundary.

This boundary is introduced to progressively move SQL concerns out of API
handlers. Existing API handlers can delegate query execution here incrementally.
"""

from typing import Any, Dict, List, Optional

from src.infrastructure.clients.database import DatabaseHandler


class DatabaseRepository:
    """Encapsulate database query execution and metadata retrieval."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler or DatabaseHandler()

    def execute_dict_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return rows as dictionaries."""
        return self.db_handler.execute_dict_query(query, params)

