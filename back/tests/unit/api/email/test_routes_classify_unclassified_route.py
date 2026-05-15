"""Unit tests for email route adapter classify_unclassified_route."""

from src.api.email.routes import classify_unclassified_route


class _HandlersOK:
    def handle_classify_unclassified(self, user_id: str, limit: int):
        return {
            "status": "ok",
            "user_id": user_id,
            "limit": limit,
            "workflow": "new",
        }


class _HandlersError:
    def handle_classify_unclassified(self, user_id: str, limit: int):
        return {"status": "error", "message": "boom"}


def test_classify_unclassified_route_success_with_query_user_id():
    result, status = classify_unclassified_route(
        handlers=_HandlersOK(),
        query={"user_id": "u-1", "limit": "10"},
    )

    assert status == 200
    assert result["status"] == "ok"
    assert result["user_id"] == "u-1"
    assert result["limit"] == 10
    assert result["workflow"] == "new"


def test_classify_unclassified_route_uses_auth_user_id_fallback():
    result, status = classify_unclassified_route(
        handlers=_HandlersOK(),
        query={"limit": "20"},
        auth_user_id="u-auth",
    )

    assert status == 200
    assert result["user_id"] == "u-auth"
    assert result["workflow"] == "new"


def test_classify_unclassified_route_requires_user_id():
    result, status = classify_unclassified_route(
        handlers=_HandlersOK(),
        query={},
        auth_user_id=None,
    )

    assert status == 400
    assert result["status"] == "error"


def test_classify_unclassified_route_returns_400_on_handler_error():
    result, status = classify_unclassified_route(
        handlers=_HandlersError(),
        query={"user_id": "u-2"},
    )

    assert status == 400
    assert result["status"] == "error"
