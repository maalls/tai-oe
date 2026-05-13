"""Tests for ServiceFactory wiring."""

from src.infrastructure.factory import ServiceFactory


def test_factory_passes_supabase_client_to_repositories(monkeypatch):
    captured = {}

    class _EmailRepo:
        def __init__(self, supabase_client=None):
            captured["email"] = supabase_client

    class _RfpRepo:
        def __init__(self, supabase_client=None):
            captured["rfp"] = supabase_client

    class _OpportunityRepo:
        def __init__(self, supabase_client=None):
            captured["opportunity"] = supabase_client

    class _VendorRepo:
        def __init__(self, supabase_client=None):
            captured["vendor"] = supabase_client

    monkeypatch.setattr("src.infrastructure.factory.SupabaseEmailRepository", _EmailRepo)
    monkeypatch.setattr("src.infrastructure.factory.SupabaseRfpRepository", _RfpRepo)
    monkeypatch.setattr("src.infrastructure.factory.SupabaseOpportunityRepository", _OpportunityRepo)
    monkeypatch.setattr("src.infrastructure.factory.SupabaseVendorRepository", _VendorRepo)

    factory = ServiceFactory(supabase_client={"db": "client"})

    factory.create_email_repository()
    factory.create_rfp_repository()
    factory.create_opportunity_repository()
    factory.create_vendor_repository()

    assert captured == {
        "email": {"db": "client"},
        "rfp": {"db": "client"},
        "opportunity": {"db": "client"},
        "vendor": {"db": "client"},
    }


def test_factory_builds_email_workflow_with_nested_services(monkeypatch):
    class _EmailService:
        def __init__(self, repository):
            self.repository = repository

    class _ClassificationService:
        def __init__(self, classifier=None):
            self.classifier = classifier

    class _WorkflowService:
        def __init__(self, email_service, classification_service):
            self.email_service = email_service
            self.classification_service = classification_service

    monkeypatch.setattr("src.infrastructure.factory.EmailService", _EmailService)
    monkeypatch.setattr("src.infrastructure.factory.ClassificationService", _ClassificationService)
    monkeypatch.setattr("src.infrastructure.factory.EmailWorkflowService", _WorkflowService)
    monkeypatch.setattr(
        "src.infrastructure.factory.SupabaseEmailRepository",
        lambda supabase_client=None: {"repo": supabase_client},
    )

    factory = ServiceFactory(supabase_client={"db": "client"})
    workflow = factory.create_email_workflow_service(classifier="mock-classifier")

    assert workflow.email_service.repository == {"repo": {"db": "client"}}
    assert workflow.classification_service.classifier == "mock-classifier"