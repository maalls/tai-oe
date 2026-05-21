import json
import os
from pathlib import Path

import pytest

from src.service.classification.service import EmailClassifier


def _require_live_llm_tests() -> None:
    if os.getenv("RUN_LLM_TESTS", "").lower() not in {"1", "true", "yes"}:
        pytest.skip("Live LLM tests disabled. Set RUN_LLM_TESTS=1 to enable.")


def test_classify_returns_normalized_category():
    _require_live_llm_tests()
    classifier = EmailClassifier()

    result = classifier.classify("Request for quotation", "Please send your prices.")

    assert isinstance(result, dict)
    assert result["category"] == "RFQ"
    assert result["reason"] is not None


def test_classify_newsletter():
    _require_live_llm_tests()
    classifier = EmailClassifier()

    result = classifier.classify(
        "Weekly Newsletter",
        "Subscribe to our latest updates and promotions!"
    )

    assert isinstance(result, dict)
    assert result["category"] == "Newsletter"
    assert result["reason"] is not None


def test_classify_other():
    _require_live_llm_tests()
    classifier = EmailClassifier()

    result = classifier.classify(
        "Meeting rescheduled",
        "The team meeting has been moved to 3pm tomorrow."
    )

    assert isinstance(result, dict)
    assert result["category"] == "Event"
    assert result["reason"] is not None


@pytest.mark.slow
def test_classifier_on_sample_emails():
    """Test classifier against sample emails with expected categories.
    
    This test makes real LLM calls and is slow. Run with: pytest -m slow
    """
    _require_live_llm_tests()
    classifier = EmailClassifier()
    
    # Load sample emails
    sample_path = Path(__file__).parent / "sample" / "sample_emails.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        emails = json.load(f)
    
    # Limit to first 3 for faster testing
    emails = emails[:10]
    
    # Test each email
    for email in emails:
        subject = email.get("subject", "")
        body = email.get("body", "")
        from_email = email.get("from", "")
        expected_category = email["classification"]["category"]
        
        # Classify the email
        result = classifier.classify(subject, body, from_email)
        
        # Assert the category matches expected
        assert result["category"] == expected_category, (
            f"Email '{subject}' was classified as '{result['category']}' "
            f"but expected '{expected_category}'. Reason: {result.get('reason')}"
        )
        assert result["reason"] is not None