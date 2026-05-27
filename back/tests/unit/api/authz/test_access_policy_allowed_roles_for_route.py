from src.api.authz.access_policy import allowed_roles_for_route


def test_allowed_roles_for_route_returns_admin_for_admin_users_list():
    roles = allowed_roles_for_route("admin.users.list")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_empty_set_for_unknown_route():
    roles = allowed_roles_for_route("unknown.route")

    assert roles == set()
