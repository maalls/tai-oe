"""Supabase implementation of the email repository contract."""

from datetime import datetime
from typing import Any, List, Optional

from domain.email import Email
from domain.enums import EmailStatus
from infrastructure.database.dto import EmailDTO
from infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from repository.contracts.email_repository import EmailRepositoryContract


class SupabaseEmailRepository(EmailRepositoryContract):
    """Email repository backed by Supabase."""

    def __init__(self, supabase_client: Optional[Any] = None):
        if supabase_client is not None:
            self.supabase = supabase_client
        else:
            # Lazy import avoids import collisions in unit tests where src is on PYTHONPATH.
            from src.supabase import get_supabase_service

            self.supabase = get_supabase_service()

    def get_by_id(self, email_id: str) -> Email:
        try:
            response = (
                self.supabase.table("email").select("*").eq("id", email_id).limit(1).execute()
            )
            if not response.data:
                raise NotFoundError(f"Email {email_id} not found")
            return self._to_domain(response.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch email {email_id}") from exc

    def get_all_unclassified(self, limit: int = 100, user_id: str | None = None) -> List[Email]:
        try:
            query = self.supabase.table("email").select("*").eq("is_classified", False)
            if user_id:
                query = query.eq("user_id", user_id)
            response = query.order("created_at", desc=True).limit(limit).execute()
            return [self._to_domain(row) for row in (response.data or [])]
        except Exception as exc:
            raise RepositoryError("Failed to fetch unclassified emails") from exc

    def save(self, email: Email) -> None:
        try:
            row = self._to_sql(email)
            self.supabase.table("email").update(row).eq("id", email.id).execute()
        except Exception as exc:
            raise RepositoryError(f"Failed to save email {email.id}") from exc

    def save_many(self, emails: List[Email]) -> None:
        try:
            rows = [self._to_sql(email) for email in emails]
            for row in rows:
                email_id = row.pop("id")
                self.supabase.table("email").update(row).eq("id", email_id).execute()
        except Exception as exc:
            raise RepositoryError("Failed to save batch emails") from exc

    def _to_domain(self, row: dict) -> Email:
        try:
            dto = EmailDTO(**row)
            status = EmailStatus.CLASSIFIED if dto.is_classified else EmailStatus.UNREAD
            return Email(
                id=dto.id,
                subject=dto.subject,
                body=dto.body_full,
                sender=dto.from_email,
                status=status,
                classification=dto.category,
                classified_at=dto.classified_at,
            )
        except Exception as exc:
            raise MappingError("Failed to map SQL row to Email domain") from exc

    def _to_sql(self, email: Email) -> dict:
        return {
            "id": email.id,
            "subject": email.subject,
            "from_email": email.sender,
            "body_full": email.body,
            "is_classified": email.status == EmailStatus.CLASSIFIED,
            "category": email.classification,
            "classified_at": datetime.utcnow().isoformat()
            if email.status == EmailStatus.CLASSIFIED
            else None,
        }
