"""Unit tests for opportunity route adapter get_opportunity_route."""

from src.api.routes.opportunity_routes import get_opportunity_route


class _HandlersOK:
    def handle_get_opportunity(self, opportunity_id: str):
        return {"status": "ok", "opportunity": {"id": opportunity_id}}


class _HandlersError:
    def handle_get_opportunity(self, opportunity_id: str):
        return {"status": "error", "message": "not found"}


def test_get_opportunity_route_success():
    result, status = get_opportunity_route(_HandlersOK(), {"opportunity_id": "opp-1"})

    assert status == 200
    assert result["status"] == "ok"
    assert result["opportunity"]["id"] == "opp-1"


def test_get_opportunity_route_requires_id():
    result, status = get_opportunity_route(_HandlersOK(), {})

    assert status == 400
    assert result["status"] == "error"


def test_get_opportunity_route_bubbles_handler_error_status():
    result, status = get_opportunity_route(_HandlersError(), {"opportunity_id": "opp-404"})

    assert status == 400
    assert result["status"] == "error"
