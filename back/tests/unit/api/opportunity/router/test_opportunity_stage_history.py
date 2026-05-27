from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.dependencies import get_database_repository, get_auth_service


class _FakeAuthService:
    def verify_token(self, authorization: str):
        if authorization == "Bearer ok":
            return True, {"id": "user-1"}
        return False, None


class _FakeDb:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}

    def execute_dict_query(self, query, params=None):
        if "FROM opportunity_state_transition" in query:
            assert params == ("opp-1", 10)
            return [
                {
                    "opportunity_id": "opp-1",
                    "from_stage": "NEW_LEAD",
                    "to_stage": "QUALIFYING",
                    "changed_by": "user-1",
                }
            ]
        return []


def test_get_opportunity_stage_history_returns_rows():
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    app.dependency_overrides[get_database_repository] = lambda: _FakeDb()
    client = TestClient(app)

    response = client.get("/api/opportunity/opp-1/stage-history", headers={"Authorization": "Bearer ok"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["to_stage"] == "QUALIFYING"