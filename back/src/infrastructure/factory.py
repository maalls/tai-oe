"""Simple service wiring factory for the new architecture."""

from infrastructure.supabase.email_supabase import SupabaseEmailRepository
from service.email.classification_service import ClassificationService
from service.email.email_service import EmailService
from service.email.workflow_service import EmailWorkflowService


class ServiceFactory:
    """Create repositories and services with injected dependencies."""

    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client

    def create_email_repository(self):
        return SupabaseEmailRepository(self.supabase_client)

    def create_email_service(self) -> EmailService:
        return EmailService(self.create_email_repository())

    def create_classification_service(self, classifier=None) -> ClassificationService:
        return ClassificationService(classifier=classifier)

    def create_email_workflow_service(self, classifier=None) -> EmailWorkflowService:
        return EmailWorkflowService(
            email_service=self.create_email_service(),
            classification_service=self.create_classification_service(classifier=classifier),
        )
