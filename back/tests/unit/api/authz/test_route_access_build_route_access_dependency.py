from fastapi.responses import JSONResponse

from src.api.authz.route_access import build_route_access_dependency


class _FakeAuthInvalid:
    def verify_token(self, auth_header: str):
        _ = auth_header
        return False, None


class _FakeAuthValid:
    def __init__(self, user_id: str):
        self._user_id = user_id

    def verify_token(self, auth_header: str):
        _ = auth_header
        return True, {"id": self._user_id}


class _FakeDbAdmin:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "admin"}


class _FakeDbUser:
    def fetch_profile(self, user_id: str):
        return {"id": user_id, "role": "user"}


def _build_dependency():
    return build_route_access_dependency(
        route_key="admin.users.list",
        unauthorized_body={"status": "error", "message": "Unauthorized"},
        forbidden_body={"status": "error", "message": "Forbidden"},
    )


def test_build_route_access_dependency_returns_unauthorized_when_token_invalid():
    dependency = _build_dependency()

    result = dependency(
        authorization=None,
        auth_service=_FakeAuthInvalid(),
        db=_FakeDbAdmin(),
    )

    assert isinstance(result, JSONResponse)
    assert result.status_code == 401


def test_build_route_access_dependency_returns_forbidden_when_role_disallowed():
    dependency = _build_dependency()

    result = dependency(
        authorization="Bearer valid",
        auth_service=_FakeAuthValid("u-user"),
        db=_FakeDbUser(),
    )

    assert isinstance(result, JSONResponse)
    assert result.status_code == 403


def test_build_route_access_dependency_returns_requester_id_when_authorized():
    dependency = _build_dependency()

    result = dependency(
        authorization="Bearer valid",
        auth_service=_FakeAuthValid("u-admin"),
        db=_FakeDbAdmin(),
    )

    assert result == "u-admin"
