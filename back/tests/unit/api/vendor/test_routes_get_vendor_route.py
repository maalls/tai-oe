"""Unit tests for vendor route adapter get_vendor_route."""

from src.api.vendor.routes import get_vendor_route


class _HandlersOK:
    def handle_get_vendor(self, vendor_id: str):
        return {"status": "ok", "vendor": {"id": vendor_id}}


class _HandlersError:
    def handle_get_vendor(self, vendor_id: str):
        return {"status": "error", "message": "not found"}


def test_get_vendor_route_success():
    result, status = get_vendor_route(_HandlersOK(), {"vendor_id": "ven-1"})

    assert status == 200
    assert result["status"] == "ok"
    assert result["vendor"]["id"] == "ven-1"


def test_get_vendor_route_requires_id():
    result, status = get_vendor_route(_HandlersOK(), {})

    assert status == 400
    assert result["status"] == "error"


def test_get_vendor_route_bubbles_handler_error_status():
    result, status = get_vendor_route(_HandlersError(), {"vendor_id": "ven-404"})

    assert status == 400
    assert result["status"] == "error"
