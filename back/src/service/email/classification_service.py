"""Service responsible for email classification orchestration."""

from typing import Any, Protocol

from domain.email import Email
from src.repository.classifier.classifier import EmailClassifier


class ClassifierClient(Protocol):
    def classify(self, title: str, body: str, from_email: str | None = None) -> Any:
        """Classify email content and return provider-specific response."""


class ClassificationService:
    """Service that normalizes classifier output to a category string."""

    def __init__(self, classifier: ClassifierClient | None = None):
        self.classifier = classifier or EmailClassifier()

    def classify_email(self, email: Email) -> str:
        raw = self.classifier.classify(
            title=email.subject or "",
            body=email.body or "",
            from_email=email.sender,
        )
        return self._extract_category(raw)

    def _extract_category(self, raw: Any) -> str:
        if isinstance(raw, str):
            return raw.strip().lower()

        if isinstance(raw, dict):
            for key in ("category", "classification", "label", "type"):
                value = raw.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()

        raise ValueError("Classifier response did not contain a valid category")
