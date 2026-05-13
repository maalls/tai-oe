"""Unit tests for opportunity route adapter advance_opportunity_route."""

from src.api.routes.opportunity_routes import advance_opportunity_route


class _HandlersOK:
    def handle_advance_opportunity(self, opportunity_id: str, stage: str):
        return {
            "status": "ok",
            "opportunity": {"id": opportunity_id, "stage": stage},
        }


class _HandlersError:
    def handle_advance_opportunity(self, opportunity_id: str, stage: str):
        return {"status": "error", "message": "invalid stage"}


def test_advance_opportunity_route_success():
    result, status = advance_opportunity_route(
        _HandlersOK(),
        {"opportunity_id": "opp-1", "stage": "NEGOTIATION"},
    )

    assert status == 200
    assert result["status"] == "ok"
    assert result["opportunity"]["stage"] == "NEGOTIATION"


def test_advance_opportunity_route_requires_id():
    result, status = advance_opportunity_route(_HandlersOK(), {"stage": "NEGOTIATION"})

    assert status == 400
    assert result["status"] == "error"


def test_advance_opportunity_route_requires_stage():
    result, status = advance_opportunity_route(_HandlersOK(), {"opportunity_id": "opp-1"})

    assert status == 400
    assert result["status"] == "error"


def test_advance_opportunity_route_bubbles_handler_error_status():
    result, status = advance_opportunity_route(
        _HandlersError(),
        {"opportunity_id": "opp-1", "stage": "BAD"},
    )

    assert status == 400
    assert result["status"] == "error"
