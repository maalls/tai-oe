"""Unit tests for handle_ddd_get_route."""

from types import SimpleNamespace

from src.api.routes.ddd_get_routes import handle_ddd_get_route, is_ddd_get_route


def test_handle_ddd_get_route_opportunity():
    handlers = SimpleNamespace(
        handle_get_opportunity=lambda opportunity_id: {
            "status": "ok",
            "opportunity": {"id": opportunity_id},
        }
    )

    handled, payload, status = handle_ddd_get_route(
        "/api/ddd/opportunity",
        {"opportunity_id": "opp-1"},
        handlers,
    )

    assert handled is True
    assert status == 200
    assert payload["opportunity"]["id"] == "opp-1"


def test_handle_ddd_get_route_opportunity_advance():
    handlers = SimpleNamespace(
        handle_advance_opportunity=lambda opportunity_id, stage: {
            "status": "ok",
            "opportunity": {"id": opportunity_id, "stage": stage},
        }
    )

    handled, payload, status = handle_ddd_get_route(
        "/api/ddd/opportunity/advance",
        {"opportunity_id": "opp-2", "stage": "NEGOTIATION"},
        handlers,
    )

    assert handled is True
    assert status == 200
    assert payload["opportunity"]["stage"] == "NEGOTIATION"


def test_handle_ddd_get_route_vendor():
    handlers = SimpleNamespace(
        handle_get_vendor=lambda vendor_id: {
            "status": "ok",
            "vendor": {"id": vendor_id},
        }
    )

    handled, payload, status = handle_ddd_get_route(
        "/api/ddd/vendor",
        {"vendor_id": "ven-1"},
        handlers,
    )

    assert handled is True
    assert status == 200
    assert payload["vendor"]["id"] == "ven-1"


def test_handle_ddd_get_route_rfp_get_and_submit():
    handlers = SimpleNamespace(
        handle_get_rfp=lambda rfp_id: {
            "status": "ok",
            "rfp": {"id": rfp_id, "status": "DRAFT"},
        },
        handle_submit_rfp=lambda rfp_id: {
            "status": "ok",
            "rfp": {"id": rfp_id, "status": "SUBMITTED"},
        },
    )

    handled_get, payload_get, status_get = handle_ddd_get_route(
        "/api/ddd/rfp",
        {"rfp_id": "rfp-1"},
        handlers,
    )
    handled_submit, payload_submit, status_submit = handle_ddd_get_route(
        "/api/ddd/rfp/submit",
        {"rfp_id": "rfp-1"},
        handlers,
    )

    assert handled_get is True
    assert status_get == 200
    assert payload_get["rfp"]["status"] == "DRAFT"

    assert handled_submit is True
    assert status_submit == 200
    assert payload_submit["rfp"]["status"] == "SUBMITTED"


def test_handle_ddd_get_route_unknown_path():
    handlers = SimpleNamespace()

    handled, payload, status = handle_ddd_get_route("/api/unknown", {}, handlers)

    assert handled is False
    assert payload == {}
    assert status == 0


def test_is_ddd_get_route_matches_supported_paths_only():
    assert is_ddd_get_route("/api/ddd/opportunity") is True
    assert is_ddd_get_route("/api/ddd/opportunity/advance") is True
    assert is_ddd_get_route("/api/ddd/vendor") is True
    assert is_ddd_get_route("/api/ddd/rfp") is True
    assert is_ddd_get_route("/api/ddd/rfp/submit") is True
    assert is_ddd_get_route("/api/ddd/unknown") is False
    assert is_ddd_get_route("/api/opportunities/search") is False
