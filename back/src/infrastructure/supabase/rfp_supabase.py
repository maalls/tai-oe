"""Supabase implementation of RFP repository contract."""

from datetime import datetime
from typing import Any, Optional

from src.domain.enums import DocumentStatus
from src.domain.rfp import Rfp
from src.infrastructure.database.dto import RfpDTO
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.rfp_repository import RfpRepositoryContract


class SupabaseRfpRepository(RfpRepositoryContract):
    """RFP repository backed by the generic document table."""

    def __init__(self, supabase_client: Optional[Any] = None):
        if supabase_client is not None:
            self.supabase = supabase_client
        else:
            from src.infrastructure.clients.supabase import get_supabase_service

            self.supabase = get_supabase_service()

    def get_by_id(self, rfp_id: str) -> Rfp:
        try:
            response = (
                self.supabase.table("document")
                .select("*")
                .eq("id", rfp_id)
                .eq("type", "RFP")
                .limit(1)
                .execute()
            )
            if not response.data:
                raise NotFoundError(f"RFP {rfp_id} not found")
            return self._to_domain(response.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch RFP {rfp_id}") from exc

    def save(self, rfp: Rfp) -> None:
        try:
            row = self._to_sql(rfp)
            self.supabase.table("document").update(row).eq("id", rfp.id).execute()
        except Exception as exc:
            raise RepositoryError(f"Failed to save RFP {rfp.id}") from exc

    def _to_domain(self, row: dict) -> Rfp:
        try:
            dto = RfpDTO(**row)
            created_at = dto.created_at
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

            return Rfp(
                id=dto.id,
                title=dto.title,
                requester_email=None,
                content=None,
                status=DocumentStatus(dto.status),
                created_at=created_at,
            )
        except Exception as exc:
            raise MappingError("Failed to map SQL row to Rfp domain") from exc

    def _to_sql(self, rfp: Rfp) -> dict:
        return {
            "id": rfp.id,
            "type": "RFP",
            "title": rfp.title,
            "status": rfp.status.value,
        }
