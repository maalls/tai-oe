"""Tests for ClassifyHandler.handle_classify."""

from src.api.classification.handler import ClassifyHandler


class _ClassifyServiceStub:
    def __init__(self):
        self.calls = []

    def handle_classify(self, email_uuid: str, user_id: str, force: bool = False):
        self.calls.append((email_uuid, user_id, force))
        return {
            "status": "ok",
            "message": "Email classified successfully",
            "result": {"category": "quote"},
        }


def test_handle_classify_delegates_to_classify_service():
    service = _ClassifyServiceStub()
    handler = ClassifyHandler(classify_service=service)

    result = handler.handle_classify("e-1", "u-1", force=True)

    assert result["status"] == "ok"
    assert result["result"]["category"] == "quote"
    assert service.calls == [("e-1", "u-1", True)]