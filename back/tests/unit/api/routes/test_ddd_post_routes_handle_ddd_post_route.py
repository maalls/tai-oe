"""Unit tests for handle_ddd_post_route."""

from types import SimpleNamespace

from src.api.routes.ddd_post_routes import handle_ddd_post_route, is_ddd_post_route


def test_handle_ddd_post_route_opportunity_advance_success():
    handlers = SimpleNamespace(
        handle_advance_opportunity=lambda opportunity_id, stage: {
            "status": "ok",
            "opportunity": {"id": opportunity_id, "stage": stage},
        }
    )

    handled, payload, status = handle_ddd_post_route(
        "/api/ddd/opportunity/advance",
        {"opportunity_id": "opp-1", "stage": "NEGOTIATION"},
        handlers,
    )

    assert handled is True
    assert status == 200
    assert payload["opportunity"]["stage"] == "NEGOTIATION"


def test_handle_ddd_post_route_rfp_submit_success():
    handlers = SimpleNamespace(
        handle_submit_rfp=lambda rfp_id: {
            "status": "ok",
            "rfp": {"id": rfp_id, "status": "SUBMITTED"},
        }
    )

    handled, payload, status = handle_ddd_post_route(
        "/api/ddd/rfp/submit",
        {"rfp_id": "rfp-1"},
        handlers,
    )

    assert handled is True
    assert status == 200
    assert payload["rfp"]["status"] == "SUBMITTED"


def test_handle_ddd_post_route_validation_error_status_is_400():
    handlers = SimpleNamespace(
        handle_advance_opportunity=lambda opportunity_id, stage: {
            "status": "error",
            "message": "bad stage",
        }
    )

    handled, payload, status = handle_ddd_post_route(
        "/api/ddd/opportunity/advance",
        {"opportunity_id": "opp-1", "stage": "BAD"},
        handlers,
    )

    assert handled is True
    assert status == 400
    assert payload["status"] == "error"


def test_handle_ddd_post_route_unknown_path():
    handlers = SimpleNamespace()

    handled, payload, status = handle_ddd_post_route("/api/ddd/unknown", {}, handlers)

    assert handled is False
    assert payload == {}
    assert status == 0


def test_is_ddd_post_route_matches_only_supported_paths():
    assert is_ddd_post_route("/api/ddd/opportunity/advance") is True
    assert is_ddd_post_route("/api/ddd/rfp/submit") is True
    assert is_ddd_post_route("/api/ddd/opportunity") is False
    assert is_ddd_post_route("/api/unknown") is False
