"""Email domain services."""

from .email_service import EmailService
from .classification_service import ClassificationService
from .workflow_service import EmailWorkflowService

__all__ = ["EmailService", "ClassificationService", "EmailWorkflowService"]
