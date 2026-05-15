"""Application service for email classification endpoint use-cases."""

from typing import Dict

class ClassifyService:
    """Service that orchestrates email classification endpoint logic."""

    def __init__(self, service_factory=None, repository=None):
        if repository is None:
            from src.repository.email_repository import EmailRepository

            repository = EmailRepository()

        if service_factory is None:
            from src.infrastructure.factory import ServiceFactory

            service_factory = ServiceFactory()

        self.repository = repository
        self.service_factory = service_factory

    def handle_classify(self, email_uuid: str, user_id: str, force: bool = False) -> Dict:
        email = self.repository.db_handler.get_email(email_uuid)
        if not email:
            return {
                "status": "error",
                "error_code": "EMAIL_NOT_FOUND",
                "message": f"Email not found: {email_uuid}",
            }

        if user_id and email.get("user_id") != user_id:
            return {
                "status": "error",
                "error_code": "UNAUTHORIZED",
                "message": "Unauthorized",
            }

        if email.get("is_classified"):
            if force:
                return self.repository.classify_email(email_uuid, user_id, force=True)

            return {
                "status": "ok",
                "message": "Email classified successfully",
                "result": {
                    "category": email.get("category"),
                    "category_suggestion": email.get("category_suggestion"),
                    "classification_reason": email.get("classification_reason"),
                    "classified_at": email.get("classified_at"),
                },
            }

        try:
            workflow = self.service_factory.create_email_workflow_service()
            workflow_result = workflow.process_new_email(email_uuid)
            updated_email = self.repository.db_handler.get_email(email_uuid) or {}
            return {
                "status": "ok",
                "message": "Email classified successfully",
                "result": {
                    "category": updated_email.get("category") or workflow_result.get("category"),
                    "category_suggestion": updated_email.get("category_suggestion"),
                    "classification_reason": updated_email.get("classification_reason"),
                    "classified_at": updated_email.get("classified_at"),
                },
            }
        except Exception as exc:
            return {
                "status": "error",
                "error_code": "CLASSIFICATION_ERROR",
                "message": f"Classification failed: {exc}",
            }
