"""SQL-backed implementation of the email repository contract."""

from datetime import datetime
from typing import List, Optional

from src.domain.email import Email
from src.domain.enums import EmailStatus
from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.infrastructure.database.dto import EmailDTO
from src.infrastructure.exceptions import MappingError, NotFoundError, RepositoryError
from src.repository.contracts.email_repository import EmailRepositoryContract


class SupabaseEmailRepository(EmailRepositoryContract):
    """Compatibility repository now backed by SQL DatabaseHandler."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def get_by_id(self, email_id: str) -> Email:
        try:
            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM email WHERE id = %s LIMIT 1",
                (email_id,),
            )
            if not rows:
                raise NotFoundError(f"Email {email_id} not found")
            return self._to_domain(rows[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch email {email_id}") from exc

    def get_all_unclassified(self, limit: int = 100, user_id: str | None = None) -> List[Email]:
        try:
            query = """
                SELECT *
                FROM email
                WHERE is_classified = FALSE
            """
            params = []
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            rows = self._get_db_handler().execute_dict_query(query, tuple(params))
            return [self._to_domain(row) for row in rows]
        except Exception as exc:
            raise RepositoryError("Failed to fetch unclassified emails") from exc

    def save(self, email: Email) -> None:
        try:
            row = self._to_sql(email)
            rows_affected = self._get_db_handler().execute_update(
                """
                UPDATE email
                SET subject = %s,
                    from_email = %s,
                    body_full = %s,
                    is_classified = %s,
                    category = %s,
                    classified_at = %s
                WHERE id = %s
                """,
                (
                    row["subject"],
                    row["from_email"],
                    row["body_full"],
                    row["is_classified"],
                    row["category"],
                    row["classified_at"],
                    email.id,
                ),
            )
            if rows_affected <= 0:
                raise NotFoundError(f"Email {email.id} not found")
        except Exception as exc:
            raise RepositoryError(f"Failed to save email {email.id}") from exc

    def save_many(self, emails: List[Email]) -> None:
        try:
            rows = [self._to_sql(email) for email in emails]
            for row in rows:
                email_id = row.pop("id")
                self._get_db_handler().execute_update(
                    """
                    UPDATE email
                    SET subject = %s,
                        from_email = %s,
                        body_full = %s,
                        is_classified = %s,
                        category = %s,
                        classified_at = %s
                    WHERE id = %s
                    """,
                    (
                        row["subject"],
                        row["from_email"],
                        row["body_full"],
                        row["is_classified"],
                        row["category"],
                        row["classified_at"],
                        email_id,
                    ),
                )
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
