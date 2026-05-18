from fastapi.testclient import TestClient

from src.api.dependencies import get_auth_service
from src.api.main import create_app
from src.api.opportunity.router import get_db


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeDb:
    def execute_dict_query(self, query, params=None):
        if "SELECT stage, status FROM opportunity" in query:
            return [{"stage": "PAID", "status": "OPEN"}]
        if "UPDATE opportunity" in query:
            assert params == ("CLOSED_WON", "WON", "opp-1")
            return [{"id": "opp-1", "stage": "CLOSED_WON", "status": "WON"}]
        if "INSERT INTO opportunity_state_transition" in query:
            assert params == ("opp-1", "PAID", "CLOSED_WON", "user-1")
            return []
        return []


class _FakeDbMissing:
    def execute_dict_query(self, query, params=None):
        if "SELECT stage, status FROM opportunity" in query:
            return []
        return []


def _client(db) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_update_opportunity_stage_state_requires_auth():
    client = _client(_FakeDb())

    response = client.put("/api/opportunity/opp-1/stage-state", json={"stage": "CLOSED_WON", "status": "WON"})

    assert response.status_code == 401


def test_update_opportunity_stage_state_returns_row():
    client = _client(_FakeDb())

    response = client.put(
        "/api/opportunity/opp-1/stage-state",
        json={"stage": "CLOSED_WON", "status": "WON"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 200
    assert response.json()["stage"] == "CLOSED_WON"
    assert response.json()["status"] == "WON"


def test_update_opportunity_stage_state_returns_404_when_missing():
    client = _client(_FakeDbMissing())

    response = client.put(
        "/api/opportunity/opp-1/stage-state",
        json={"stage": "CLOSED_WON", "status": "WON"},
        headers={"Authorization": "Bearer ok"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found"