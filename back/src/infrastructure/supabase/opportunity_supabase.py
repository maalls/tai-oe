"""Supabase implementation of opportunity repository contract."""

from typing import Any, List, Optional

from src.domain.enums import OpportunityStage, OpportunityStatus
from src.domain.opportunity import Opportunity
from src.infrastructure.database.dto import OpportunityDTO
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.opportunity_repository import OpportunityRepositoryContract


class SupabaseOpportunityRepository(OpportunityRepositoryContract):
    """Opportunity repository backed by Supabase."""

    def __init__(self, supabase_client: Optional[Any] = None):
        if supabase_client is not None:
            self.supabase = supabase_client
        else:
            from src.supabase import get_supabase_service

            self.supabase = get_supabase_service()

    def get_by_id(self, opportunity_id: str) -> Opportunity:
        try:
            response = (
                self.supabase.table("opportunity")
                .select("*")
                .eq("id", opportunity_id)
                .limit(1)
                .execute()
            )
            if not response.data:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            return self._to_domain(response.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch opportunity {opportunity_id}") from exc

    def save(self, opportunity: Opportunity) -> None:
        try:
            row = self._to_sql(opportunity)
            self.supabase.table("opportunity").update(row).eq("id", opportunity.id).execute()
        except Exception as exc:
            raise RepositoryError(f"Failed to save opportunity {opportunity.id}") from exc

    def get_open_by_user(self, user_id: str, limit: int = 100) -> List[Opportunity]:
        try:
            response = (
                self.supabase.table("opportunity")
                .select("*")
                .eq("owner_user_id", user_id)
                .eq("status", OpportunityStatus.OPEN.value)
                .limit(limit)
                .execute()
            )
            return [self._to_domain(row) for row in (response.data or [])]
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch open opportunities for user {user_id}") from exc

    def _to_domain(self, row: dict) -> Opportunity:
        try:
            dto = OpportunityDTO(**row)
            return Opportunity(
                id=dto.id,
                owner_user_id=dto.owner_user_id,
                account_id=dto.account_id,
                name=dto.name,
                stage=OpportunityStage(dto.stage),
                status=OpportunityStatus(dto.status),
                amount_estimated=float(dto.amount_estimated or 0),
                probability=int(dto.probability or 0),
                expected_close_date=dto.expected_close_date,
                source=dto.source,
                source_reference_id=dto.source_reference_id,
                created_at=dto.created_at,
            )
        except Exception as exc:
            raise MappingError("Failed to map SQL row to Opportunity domain") from exc

    def _to_sql(self, opportunity: Opportunity) -> dict:
        return {
            "id": opportunity.id,
            "owner_user_id": opportunity.owner_user_id,
            "account_id": opportunity.account_id,
            "name": opportunity.name,
            "stage": opportunity.stage.value,
            "status": opportunity.status.value,
            "amount_estimated": opportunity.amount_estimated,
            "probability": opportunity.probability,
            "expected_close_date": opportunity.expected_close_date.isoformat()
            if opportunity.expected_close_date
            else None,
            "source": opportunity.source,
            "source_reference_id": opportunity.source_reference_id,
        }
