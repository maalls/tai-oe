"""Unit tests for RFP route adapter submit_rfp_route."""

from src.api.rfq.routes import submit_rfp_route


class _HandlersOK:
    def handle_submit_rfp(self, rfp_id: str):
        return {"status": "ok", "rfp": {"id": rfp_id, "status": "SUBMITTED"}}


class _HandlersError:
    def handle_submit_rfp(self, rfp_id: str):
        return {"status": "error", "message": "already submitted"}


def test_submit_rfp_route_success():
    result, status = submit_rfp_route(_HandlersOK(), {"rfp_id": "rfp-1"})

    assert status == 200
    assert result["status"] == "ok"
    assert result["rfp"]["status"] == "SUBMITTED"


def test_submit_rfp_route_requires_id():
    result, status = submit_rfp_route(_HandlersOK(), {})

    assert status == 400
    assert result["status"] == "error"


def test_submit_rfp_route_bubbles_handler_error_status():
    result, status = submit_rfp_route(_HandlersError(), {"rfp_id": "rfp-1"})

    assert status == 400
    assert result["status"] == "error"
