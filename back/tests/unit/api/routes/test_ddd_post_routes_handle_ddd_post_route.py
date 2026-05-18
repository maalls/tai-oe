"""Unit tests for handle_ddd_post_route."""

from src.api.routes.ddd_post_routes import handle_ddd_post_route, is_ddd_post_route


def test_handle_ddd_post_route_returns_unhandled_for_retired_legacy_paths():
    handled, payload, status = handle_ddd_post_route("/api/ddd/opportunity/advance", {}, handlers=object())

    assert handled is False
    assert payload == {}
    assert status == 0


def test_is_ddd_post_route_is_false_for_any_path_with_empty_route_map():
    assert is_ddd_post_route("/api/ddd/opportunity/advance") is False
    assert is_ddd_post_route("/api/ddd/rfp/submit") is False
    assert is_ddd_post_route("/api/unknown") is False
