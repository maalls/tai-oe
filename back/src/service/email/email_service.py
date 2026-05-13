"""Application service for email read/update use-cases."""

from domain.email import Email
from repository.contracts.email_repository import EmailRepositoryContract


class EmailService:
    """Service orchestrating email operations via repository contract."""

    def __init__(self, email_repository: EmailRepositoryContract):
        self.repo = email_repository

    def get_email(self, email_id: str) -> Email:
        return self.repo.get_by_id(email_id)

    def get_all_unclassified(self, limit: int = 100, user_id: str | None = None) -> list[Email]:
        return self.repo.get_all_unclassified(limit=limit, user_id=user_id)

    def mark_classified(self, email_id: str, category: str) -> Email:
        email = self.repo.get_by_id(email_id)
        classified = email.mark_classified(category)
        self.repo.save(classified)
        return classified
