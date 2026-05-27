"""Profile-oriented repository operations."""

from __future__ import annotations

from typing import Any, Dict, Optional


class ProfileRepositoryMixin:
    """Database profile read/update operations."""

    def fetch_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT id, email, full_name, role FROM profile WHERE id = %s LIMIT 1"
        rows = self.execute_dict_query(query, (user_id,))
        return rows[0] if rows else None

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses = []
        params = []
        if "full_name" in updates:
            set_clauses.append("full_name = %s")
            params.append(updates["full_name"])
        if not set_clauses:
            return self.fetch_profile(user_id)
        params.append(user_id)
        query = f"UPDATE profile SET {', '.join(set_clauses)} WHERE id = %s RETURNING id, email, full_name, role"
        rows = self.execute_dict_query(query, tuple(params))
        return rows[0] if rows else None
