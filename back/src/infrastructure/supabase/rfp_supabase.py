"""SQL-backed implementation of RFP repository contract."""

from datetime import datetime
from typing import Any, Optional

from src.domain.enums import DocumentStatus
from src.domain.rfp import Rfp
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.infrastructure.database.dto import RfpDTO
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.rfp_repository import RfpRepositoryContract


class SupabaseRfpRepository(RfpRepositoryContract):
    """Compatibility repository now backed by SQL document table."""

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

    def get_by_id(self, rfp_id: str) -> Rfp:
        try:
            rows = self._get_db_handler().execute_dict_query(
                """
                SELECT *
                FROM document
                WHERE id = %s
                  AND type = 'RFP'
                LIMIT 1
                """,
                (rfp_id,),
            )
            if not rows:
                raise NotFoundError(f"RFP {rfp_id} not found")
            return self._to_domain(rows[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch RFP {rfp_id}") from exc

    def save(self, rfp: Rfp) -> None:
        try:
            row = self._to_sql(rfp)
            rows_affected = self._get_db_handler().execute_update(
                """
                UPDATE document
                SET type = %s,
                    title = %s,
                    status = %s
                WHERE id = %s
                """,
                (row["type"], row["title"], row["status"], rfp.id),
            )
            if rows_affected <= 0:
                raise NotFoundError(f"RFP {rfp.id} not found")
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
