"""SQL-backed implementation of vendor repository contract."""

from datetime import datetime
from typing import Any, Optional

from src.domain.vendor import Vendor
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.vendor_repository import VendorRepositoryContract


class SupabaseVendorRepository(VendorRepositoryContract):
    """Compatibility repository now backed by SQL DatabaseHandler."""

    def __init__(self, supabase_client: Optional[Any] = None, db_handler: Optional[DatabaseHandler] = None):
        if db_handler is not None:
            self.db_handler = db_handler
        elif supabase_client is not None and hasattr(supabase_client, "execute_dict_query"):
            self.db_handler = supabase_client
        else:
            self.db_handler = None

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def get_by_id(self, vendor_id: str) -> Vendor:
        try:
            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM vendor WHERE id = %s LIMIT 1",
                (vendor_id,),
            )
            if not rows:
                raise NotFoundError(f"Vendor {vendor_id} not found")
            return self._to_domain(rows[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch vendor {vendor_id}") from exc

    def save(self, vendor: Vendor) -> None:
        try:
            row = self._to_sql(vendor)
            rows_affected = self._get_db_handler().execute_update(
                """
                UPDATE vendor
                SET name = %s,
                    email = %s,
                    phone = %s,
                    website = %s
                WHERE id = %s
                """,
                (row["name"], row["email"], row["phone"], row["website"], vendor.id),
            )
            if rows_affected <= 0:
                raise NotFoundError(f"Vendor {vendor.id} not found")
        except Exception as exc:
            raise RepositoryError(f"Failed to save vendor {vendor.id}") from exc

    def _to_domain(self, row: dict) -> Vendor:
        try:
            created_at = row.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            return Vendor(
                id=str(row["id"]),
                name=row["name"],
                email=row.get("email"),
                phone=row.get("phone"),
                website=row.get("website"),
                created_at=created_at,
            )
        except Exception as exc:
            raise MappingError("Failed to map SQL row to Vendor domain") from exc

    def _to_sql(self, vendor: Vendor) -> dict:
        return {
            "id": vendor.id,
            "name": vendor.name,
            "email": vendor.email,
            "phone": vendor.phone,
            "website": vendor.website,
        }
