"""Simple service wiring factory for the new architecture."""

from src.infrastructure.supabase.opportunity_supabase import SupabaseOpportunityRepository
from src.infrastructure.supabase.rfp_supabase import SupabaseRfpRepository
from src.infrastructure.supabase.email_supabase import SupabaseEmailRepository
from src.infrastructure.supabase.vendor_supabase import SupabaseVendorRepository
from src.service.opportunity.opportunity_service import OpportunityService
from src.service.rfp.rfp_service import RfpService
from src.service.email.classification_service import ClassificationService
from src.service.email.email_service import EmailService
from src.service.email.workflow_service import EmailWorkflowService
from src.service.vendor.vendor_service import VendorService


class ServiceFactory:
    """Create repositories and services with injected dependencies."""

    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client

    def create_email_repository(self):
        return SupabaseEmailRepository(self.supabase_client)

    def create_rfp_repository(self):
        return SupabaseRfpRepository(self.supabase_client)

    def create_opportunity_repository(self):
        return SupabaseOpportunityRepository(self.supabase_client)

    def create_vendor_repository(self):
        return SupabaseVendorRepository(self.supabase_client)

    def create_email_service(self) -> EmailService:
        return EmailService(self.create_email_repository())

    def create_rfp_service(self) -> RfpService:
        return RfpService(self.create_rfp_repository())

    def create_opportunity_service(self) -> OpportunityService:
        return OpportunityService(self.create_opportunity_repository())

    def create_vendor_service(self) -> VendorService:
        return VendorService(self.create_vendor_repository())

    def create_classification_service(self, classifier=None) -> ClassificationService:
        return ClassificationService(classifier=classifier)

    def create_email_workflow_service(self, classifier=None) -> EmailWorkflowService:
        return EmailWorkflowService(
            email_service=self.create_email_service(),
            classification_service=self.create_classification_service(classifier=classifier),
        )
