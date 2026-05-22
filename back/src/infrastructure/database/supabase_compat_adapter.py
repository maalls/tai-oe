"""Compatibility adapter exposing a minimal Supabase-like table API over DatabaseHandler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import re

from src.infrastructure.clients.database import DatabaseHandler


_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _assert_safe_identifier(value: str) -> str:
    if not _SAFE_IDENTIFIER_RE.match(value):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return value


@dataclass
class CompatResponse:
    data: Any = None
    error: str | None = None


class _TableQuery:
    def __init__(self, db_handler: DatabaseHandler, table_name: str):
        self._db_handler = db_handler
        self._table_name = _assert_safe_identifier(table_name)
        self._action = "select"
        self._select_columns = "*"
        self._update_payload: dict[str, Any] | None = None
        self._insert_payload: dict[str, Any] | list[dict[str, Any]] | None = None
        self._upsert_payload: list[dict[str, Any]] | None = None
        self._upsert_on_conflict: tuple[str, ...] = ()
        self._filters: list[tuple[str, str, Any]] = []
        self._limit: int | None = None
        self._order_by: tuple[str, bool] | None = None
        self._single = False

    def select(self, columns: str):
        self._action = "select"
        self._select_columns = columns or "*"
        return self

    def insert(self, payload: dict[str, Any] | list[dict[str, Any]]):
        self._action = "insert"
        self._insert_payload = payload
        return self

    def update(self, payload: dict[str, Any]):
        self._action = "update"
        self._update_payload = payload
        return self

    def delete(self):
        self._action = "delete"
        return self

    def upsert(self, payload: list[dict[str, Any]], on_conflict: str):
        self._action = "upsert"
        self._upsert_payload = payload
        self._upsert_on_conflict = tuple(
            _assert_safe_identifier(col.strip()) for col in (on_conflict or "").split(",") if col.strip()
        )
        return self

    def eq(self, key: str, value: Any):
        self._filters.append((_assert_safe_identifier(key), "=", value))
        return self

    def ilike(self, key: str, value: Any):
        self._filters.append((_assert_safe_identifier(key), "ILIKE", value))
        return self

    def in_(self, key: str, values: Iterable[Any]):
        self._filters.append((_assert_safe_identifier(key), "IN", tuple(values)))
        return self

    def order(self, key: str, desc: bool = False):
        self._order_by = (_assert_safe_identifier(key), bool(desc))
        return self

    def limit(self, value: int):
        self._limit = int(value)
        return self

    def single(self):
        self._single = True
        return self

    def _build_where(self, params: list[Any]) -> str:
        if not self._filters:
            return ""

        clauses: list[str] = []
        for key, op, value in self._filters:
            if op == "IN":
                values = list(value)
                if not values:
                    clauses.append("1 = 0")
                    continue
                placeholders = ", ".join(["%s"] * len(values))
                clauses.append(f"{key} IN ({placeholders})")
                params.extend(values)
                continue

            clauses.append(f"{key} {op} %s")
            params.append(value)

        return " WHERE " + " AND ".join(clauses)

    def execute(self) -> CompatResponse:
        try:
            if self._action == "select":
                params: list[Any] = []
                where_clause = self._build_where(params)
                order_clause = ""
                if self._order_by is not None:
                    col, desc = self._order_by
                    order_clause = f" ORDER BY {col} {'DESC' if desc else 'ASC'}"
                limit_clause = ""
                if self._limit is not None:
                    limit_clause = " LIMIT %s"
                    params.append(self._limit)

                query = (
                    f"SELECT {self._select_columns} "
                    f"FROM {self._table_name}"
                    f"{where_clause}{order_clause}{limit_clause}"
                )
                rows = self._db_handler.execute_dict_query(query, tuple(params))
                if self._single:
                    return CompatResponse(data=rows[0] if rows else None)
                return CompatResponse(data=rows)

            if self._action == "insert":
                payload = self._insert_payload
                if payload is None:
                    return CompatResponse(data=[], error="insert payload is required")
                rows_payload = payload if isinstance(payload, list) else [payload]
                inserted: list[dict[str, Any]] = []
                for row in rows_payload:
                    columns = [_assert_safe_identifier(col) for col in row.keys()]
                    values = [row[col] for col in row.keys()]
                    query = (
                        f"INSERT INTO {self._table_name} ({', '.join(columns)}) "
                        f"VALUES ({', '.join(['%s'] * len(columns))}) RETURNING *"
                    )
                    inserted.extend(self._db_handler.execute_dict_query(query, tuple(values)))
                return CompatResponse(data=inserted)

            if self._action == "update":
                payload = self._update_payload or {}
                if not payload:
                    return CompatResponse(data=[], error="update payload is required")
                params: list[Any] = []
                set_parts: list[str] = []
                for key, value in payload.items():
                    set_parts.append(f"{_assert_safe_identifier(key)} = %s")
                    params.append(value)
                where_clause = self._build_where(params)
                query = (
                    f"UPDATE {self._table_name} SET {', '.join(set_parts)}"
                    f"{where_clause} RETURNING *"
                )
                rows = self._db_handler.execute_dict_query(query, tuple(params))
                return CompatResponse(data=rows)

            if self._action == "delete":
                params: list[Any] = []
                where_clause = self._build_where(params)
                query = f"DELETE FROM {self._table_name}{where_clause} RETURNING *"
                rows = self._db_handler.execute_dict_query(query, tuple(params))
                return CompatResponse(data=rows)

            if self._action == "upsert":
                payload_rows = self._upsert_payload or []
                if not payload_rows:
                    return CompatResponse(data=[])
                if not self._upsert_on_conflict:
                    return CompatResponse(data=[], error="upsert on_conflict is required")

                inserted: list[dict[str, Any]] = []
                for row in payload_rows:
                    columns = [_assert_safe_identifier(col) for col in row.keys()]
                    values = [row[col] for col in row.keys()]
                    conflict_cols = ", ".join(self._upsert_on_conflict)
                    conflict_set = [
                        col for col in columns if col not in self._upsert_on_conflict
                    ]
                    set_clause = ", ".join(
                        [f"{col} = EXCLUDED.{col}" for col in conflict_set]
                    )
                    if not set_clause:
                        set_clause = f"{self._upsert_on_conflict[0]} = EXCLUDED.{self._upsert_on_conflict[0]}"

                    query = (
                        f"INSERT INTO {self._table_name} ({', '.join(columns)}) "
                        f"VALUES ({', '.join(['%s'] * len(columns))}) "
                        f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {set_clause} "
                        f"RETURNING *"
                    )
                    inserted.extend(self._db_handler.execute_dict_query(query, tuple(values)))
                return CompatResponse(data=inserted)

            return CompatResponse(data=[], error=f"Unsupported action: {self._action}")
        except Exception as exc:  # pragma: no cover - compatibility guard
            return CompatResponse(data=[], error=str(exc))


class SupabaseCompatAdapter:
    """Adapter that offers a Supabase-like `table(...).execute()` API on top of SQL."""

    def __init__(self, db_handler: DatabaseHandler):
        self._db_handler = db_handler

    def table(self, table_name: str) -> _TableQuery:
        return _TableQuery(self._db_handler, table_name)
