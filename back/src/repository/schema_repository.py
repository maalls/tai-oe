"""Schema browsing/query helpers for CSV and diagnostics endpoints."""

from __future__ import annotations

from typing import Any, Dict, List

from src.repository.core_repository import CoreDatabaseRepository


class SchemaRepository(CoreDatabaseRepository):
    """Schema metadata and dynamic query operations."""

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
