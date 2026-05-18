"""Database query repository boundary.

This boundary is introduced to progressively move SQL concerns out of API
handlers. Existing API handlers can delegate query execution here incrementally.
"""

from typing import Any, Dict, List, Optional

from src.infrastructure.clients.database import DatabaseHandler


class DatabaseRepository:

        def fetch_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
            query = "SELECT id, email, full_name FROM profile WHERE id = %s LIMIT 1"
            rows = self.execute_dict_query(query, (user_id,))
            return rows[0] if rows else None

        def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # Only allow updating full_name for now
            set_clauses = []
            params = []
            if 'full_name' in updates:
                set_clauses.append('full_name = %s')
                params.append(updates['full_name'])
            if not set_clauses:
                return self.fetch_profile(user_id)
            params.append(user_id)
            query = f"UPDATE profile SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, email, full_name"
            rows = self.execute_dict_query(query, tuple(params))
            return rows[0] if rows else None
    """Encapsulate database query execution and metadata retrieval."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler or DatabaseHandler()

    def execute_dict_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return rows as dictionaries."""
        return self.db_handler.execute_dict_query(query, params)

    def list_public_tables_with_columns(self) -> List[Dict[str, Any]]:
        """Return public tables enriched with column metadata."""
        query = """
            SELECT
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c
                ON t.table_name = c.table_name
                AND t.table_schema = c.table_schema
            WHERE t.table_schema = 'public'
            ORDER BY t.table_name, c.ordinal_position;
        """
        return self.execute_dict_query(query)

    def query_table(
        self,
        table: str,
        columns_raw: str = "*",
        where_clause: str = "",
        sort_by: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Run a dynamic table query using current legacy query-shaping rules."""
        columns = columns_raw if columns_raw != "*" else "*"
        query = f"SELECT {columns} FROM {table}"

        if where_clause:
            query += f" WHERE {where_clause}"
        if sort_by:
            query += f" ORDER BY {sort_by}"

        query += f" LIMIT {limit} OFFSET {offset}"
        return self.execute_dict_query(query)

