"""Generic entity update handlers."""

from typing import Dict
import re

from src.infrastructure.clients.supabase import get_supabase_service


class EntityHandlers:
    """Handle transversal entity operations."""

    def __init__(self, supabase=None):
        self.supabase = supabase or get_supabase_service()

    def handle_update_entity_field(self, table: str, field: str, record_id: str, value, user_id: str = None) -> Dict:
        """Update a single field on a table by record id."""
        _ = user_id
        try:
            if not table or not field:
                return {"status": "error", "message": "Missing table or field"}

            name_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
            if not name_re.match(table) or not name_re.match(field):
                return {"status": "error", "message": "Invalid table or field"}

            if not record_id:
                return {"status": "error", "message": "Missing id"}

            update_resp = self.supabase.table(table).update({field: value}).eq("id", record_id).execute()

            if getattr(update_resp, "error", None):
                return {"status": "error", "message": f"Failed to update: {update_resp.error}"}

            if not update_resp.data:
                return {"status": "error", "message": "No rows updated"}

            return {"status": "ok", "data": update_resp.data[0]}

        except Exception as e:  # noqa: BLE001
            print(f"[EntityHandlers] Error in handle_update_entity_field: {e}")
            return {"status": "error", "message": str(e)}
