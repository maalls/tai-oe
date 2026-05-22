"""SQL-backed implementation of opportunity repository contract."""

from typing import Any, List, Optional

from src.domain.enums import OpportunityStage, OpportunityStatus
from src.domain.opportunity import Opportunity
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.infrastructure.database.dto import OpportunityDTO
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.opportunity_repository import OpportunityRepositoryContract


class SupabaseOpportunityRepository(OpportunityRepositoryContract):
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

    def get_by_id(self, opportunity_id: str) -> Opportunity:
        try:
            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM opportunity WHERE id = %s LIMIT 1",
                (opportunity_id,),
            )
            if not rows:
                raise NotFoundError(f"Opportunity {opportunity_id} not found")
            return self._to_domain(rows[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch opportunity {opportunity_id}") from exc

    def save(self, opportunity: Opportunity) -> None:
        try:
            row = self._to_sql(opportunity)
            rows_affected = self._get_db_handler().execute_update(
                """
                UPDATE opportunity
                SET owner_user_id = %s,
                    account_id = %s,
                    name = %s,
                    stage = %s,
                    status = %s,
                    amount_estimated = %s,
                    probability = %s,
                    expected_close_date = %s,
                    source = %s,
                    source_reference_id = %s
                WHERE id = %s
                """,
                (
                    row["owner_user_id"],
                    row["account_id"],
                    row["name"],
                    row["stage"],
                    row["status"],
                    row["amount_estimated"],
                    row["probability"],
                    row["expected_close_date"],
                    row["source"],
                    row["source_reference_id"],
                    opportunity.id,
                ),
            )
            if rows_affected <= 0:
                raise NotFoundError(f"Opportunity {opportunity.id} not found")
        except Exception as exc:
            raise RepositoryError(f"Failed to save opportunity {opportunity.id}") from exc

    def get_open_by_user(self, user_id: str, limit: int = 100) -> List[Opportunity]:
        try:
            rows = self._get_db_handler().execute_dict_query(
                """
                SELECT *
                FROM opportunity
                WHERE owner_user_id = %s
                  AND status = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, OpportunityStatus.OPEN.value, limit),
            )
            return [self._to_domain(row) for row in rows]
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
