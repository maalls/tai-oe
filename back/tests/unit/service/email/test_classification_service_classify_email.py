"""Unit tests for ClassificationService.classify_email."""

import pytest

from service.email.classification_service import ClassificationService
from tests.fixtures.sample_data import sample_email


class _FakeClassifier:
    def __init__(self, response):
        self.response = response

    def classify(self, title: str, body: str, from_email=None):
        return self.response


def test_classify_email_uses_category_key():
    service = ClassificationService(classifier=_FakeClassifier({"category": "Quote"}))
    result = service.classify_email(sample_email())
    assert result == "quote"


def test_classify_email_accepts_raw_string_response():
    service = ClassificationService(classifier=_FakeClassifier("RFP"))
    result = service.classify_email(sample_email())
    assert result == "rfp"


def test_classify_email_raises_on_invalid_payload():
    service = ClassificationService(classifier=_FakeClassifier({"foo": "bar"}))
    with pytest.raises(ValueError):
        service.classify_email(sample_email())
