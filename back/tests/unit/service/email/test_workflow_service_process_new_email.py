"""Unit tests for EmailWorkflowService.process_new_email."""

from service.email.classification_service import ClassificationService
from service.email.email_service import EmailService
from service.email.workflow_service import EmailWorkflowService
from tests.fixtures.sample_data import sample_email


class _ClassifierQuote:
    def classify(self, title: str, body: str, from_email=None):
        return {"category": "quote"}


def test_process_new_email_classifies_and_saves(fake_email_repo):
    email = sample_email(id="e-workflow")
    fake_email_repo.save(email)

    email_service = EmailService(fake_email_repo)
    classification_service = ClassificationService(classifier=_ClassifierQuote())
    workflow = EmailWorkflowService(email_service, classification_service)

    result = workflow.process_new_email("e-workflow")

    assert result["email_id"] == "e-workflow"
    assert result["category"] == "quote"
    assert result["status"] == "classified"
    assert fake_email_repo.get_by_id("e-workflow").classification == "quote"
