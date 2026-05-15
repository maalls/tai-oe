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

    def classify_unclassified(self, user_id: str, limit: int = 200) -> dict:
        """Classify pending emails for a user and report per-item errors."""
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
            }

        try:
            emails = self.email_service.get_all_unclassified(limit=limit, user_id=user_id)

            classified = 0
            errors = []
            for email in emails:
                try:
                    self.process_new_email(email.id)
                    classified += 1
                except Exception as exc:
                    errors.append({"email_id": email.id, "error": str(exc)})

            return {
                "status": "ok",
                "workflow": "new",
                "classified": classified,
                "skipped": len(errors),
                "errors": errors,
            }
        except Exception as exc:
            return {
                "status": "error",
                "workflow": "new",
                "message": f"New workflow failed: {exc}",
            }
