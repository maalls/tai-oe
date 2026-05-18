"""Unit tests for handle_ddd_get_route."""

from src.api.routes.ddd_get_routes import handle_ddd_get_route, is_ddd_get_route


def test_handle_ddd_get_route_returns_unhandled_for_retired_legacy_paths():
    handled, payload, status = handle_ddd_get_route("/api/ddd/opportunity", {}, handlers=object())

    assert handled is False
    assert payload == {}
    assert status == 0


def test_is_ddd_get_route_is_false_for_any_path_with_empty_route_map():
    assert is_ddd_get_route("/api/ddd/opportunity") is False
    assert is_ddd_get_route("/api/ddd/rfp") is False
    assert is_ddd_get_route("/api/unknown") is False
