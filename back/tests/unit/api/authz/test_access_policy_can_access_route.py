from src.api.authz.access_policy import can_access_route


def test_can_access_route_returns_true_for_admin_on_admin_route():
    assert can_access_route("admin", "/api/admin/users") is True


def test_can_access_route_returns_false_for_user_on_admin_route():
    assert can_access_route("user", "/api/admin/users") is False


def test_can_access_route_returns_false_when_role_missing():
    assert can_access_route(None, "/api/admin/users") is False
