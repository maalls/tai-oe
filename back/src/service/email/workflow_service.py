"""Workflow service for end-to-end email processing."""

from src.service.email.classification_service import ClassificationService
from src.service.email.email_service import EmailService


class EmailWorkflowService:
    """Coordinates fetching, classifying and saving email state."""

    def __init__(self, email_service: EmailService, classification_service: ClassificationService):
        self.email_service = email_service
        self.classification_service = classification_service

    def process_new_email(self, email_id: str) -> dict:
        email = self.email_service.get_email(email_id)
        category = self.classification_service.classify_email(email)
        updated = self.email_service.mark_classified(email_id, category)
        return {
            "email_id": updated.id,
            "category": category,
            "status": updated.status.value,
        }
