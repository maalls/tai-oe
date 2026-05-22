"""Core repository primitives shared by database repositories."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.infrastructure.clients.database import DatabaseHandler


class CoreDatabaseRepository:
    """Core SQL execution boundary over DatabaseHandler."""

    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def execute_dict_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return rows as dictionaries."""
        return self.db_handler.execute_dict_query(query, params)
