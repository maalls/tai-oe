from src.api.authz.access_policy import allowed_roles_for_route


def test_allowed_roles_for_route_returns_admin_for_admin_users_list():
    roles = allowed_roles_for_route("/api/admin/users")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_admin_for_csv_query():
    roles = allowed_roles_for_route("/api/csv/query")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_admin_for_csv_access():
    roles = allowed_roles_for_route("/api/csv/sources")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_admin_for_utils_prompt_read():
    roles = allowed_roles_for_route("/api/prompt/{relative_path:path}")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_admin_for_email_fetch_loop_status():
    roles = allowed_roles_for_route("/api/email-fetch-loop/status")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_admin_for_unsafe_utils_route():
    roles = allowed_roles_for_route("/api/fetch")

    assert roles == {"admin"}


def test_allowed_roles_for_route_returns_admin_and_user_for_storage_read():
    roles = allowed_roles_for_route("/api/storage/{raw_filename:path}")

    assert roles == {"admin", "user"}


def test_allowed_roles_for_route_returns_admin_for_action_execute_and_logs_routes():
    assert allowed_roles_for_route("/api/action/{action_id}/execute") == {"admin"}
    assert allowed_roles_for_route("/api/actions/{action_id}/execute") == {"admin"}
    assert allowed_roles_for_route("/api/actions/{action_id}/logs") == {"admin"}


def test_allowed_roles_for_route_returns_empty_set_for_unknown_route():
    roles = allowed_roles_for_route("/api/unknown")

    assert roles == set()
