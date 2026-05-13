"""Supabase implementation of vendor repository contract."""

from datetime import datetime
from typing import Any, Optional

from src.domain.vendor import Vendor
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.vendor_repository import VendorRepositoryContract


class SupabaseVendorRepository(VendorRepositoryContract):
    """Vendor repository backed by Supabase."""

    def __init__(self, supabase_client: Optional[Any] = None):
        if supabase_client is not None:
            self.supabase = supabase_client
        else:
            from src.supabase import get_supabase_service

            self.supabase = get_supabase_service()

    def get_by_id(self, vendor_id: str) -> Vendor:
        try:
            response = (
                self.supabase.table("vendor").select("*").eq("id", vendor_id).limit(1).execute()
            )
            if not response.data:
                raise NotFoundError(f"Vendor {vendor_id} not found")
            return self._to_domain(response.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch vendor {vendor_id}") from exc

    def save(self, vendor: Vendor) -> None:
        try:
            row = self._to_sql(vendor)
            self.supabase.table("vendor").update(row).eq("id", vendor.id).execute()
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
