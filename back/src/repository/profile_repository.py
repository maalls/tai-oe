from __future__ import annotations

from typing import Any, Dict, Optional

from src.repository.core_repository import CoreDatabaseRepository



class ProfileRepository(CoreDatabaseRepository):
    """Database profile read/update operations."""

    _ALLOWED_ROLES = {"admin", "user"}

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

    def list_users(self, limit: int = 100, offset: int = 0) -> list[Dict[str, Any]]:
        query = (
            "SELECT id, email, full_name, role, created_at "
            "FROM profile "
            "ORDER BY created_at DESC "
            "LIMIT %s OFFSET %s"
        )
        return self.execute_dict_query(query, (limit, offset))

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = (
            "SELECT id, email, full_name, role, created_at "
            "FROM profile "
            "WHERE id = %s "
            "LIMIT 1"
        )
        rows = self.execute_dict_query(query, (user_id,))
        return rows[0] if rows else None

    def set_user_role(self, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        if role not in self._ALLOWED_ROLES:
            raise ValueError("Invalid role")

        query = (
            "UPDATE profile "
            "SET role = %s "
            "WHERE id = %s "
            "RETURNING id, email, full_name, role, created_at"
        )
        rows = self.execute_dict_query(query, (role, user_id))
        return rows[0] if rows else None

    def insert_profile(self, user_id: str, email: str, full_name: str = None, role: str = "user") -> Optional[Dict[str, Any]]:
        query = (
            "INSERT INTO profile (id, email, full_name, role) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING "
            "RETURNING id, email, full_name, role, created_at"
        )
        params = (user_id, email, full_name, role)
        rows = self.execute_dict_query(query, params)
        if rows:
            return rows[0]
        return self.get_user_by_id(user_id)
