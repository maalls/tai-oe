"""Unit tests for RFP route adapter get_rfp_route."""

from src.api.routes.rfp_routes import get_rfp_route


class _HandlersOK:
    def handle_get_rfp(self, rfp_id: str):
        return {"status": "ok", "rfp": {"id": rfp_id}}


class _HandlersError:
    def handle_get_rfp(self, rfp_id: str):
        return {"status": "error", "message": "not found"}


def test_get_rfp_route_success():
    result, status = get_rfp_route(_HandlersOK(), {"rfp_id": "rfp-1"})

    assert status == 200
    assert result["status"] == "ok"
    assert result["rfp"]["id"] == "rfp-1"


def test_get_rfp_route_requires_id():
    result, status = get_rfp_route(_HandlersOK(), {})

    assert status == 400
    assert result["status"] == "error"


def test_get_rfp_route_bubbles_handler_error_status():
    result, status = get_rfp_route(_HandlersError(), {"rfp_id": "rfp-404"})

    assert status == 400
    assert result["status"] == "error"
