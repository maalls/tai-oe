from src.api.routes.helpers.server_query_helpers import get_payload_int, get_qs_bool, get_qs_int, get_qs_value
from src.api.routes.helpers.server_status_helpers import pop_status, status_from_error, status_from_result


def test_status_from_result_maps_ok_and_error():
    assert status_from_result({"status": "ok"}) == 200
    assert status_from_result({"status": "error"}) == 400


def test_pop_status_extracts_and_removes_code():
    payload = {"status": 201, "value": "x"}

    code = pop_status(payload, default=200)

    assert code == 201
    assert payload == {"value": "x"}


def test_status_from_error_detects_error_key():
    assert status_from_error({"error": "boom"}) == 400
    assert status_from_error({"value": "ok"}) == 200


def test_get_qs_int_and_default_behavior():
    assert get_qs_int({"limit": ["12"]}, "limit", 5) == 12
    assert get_qs_int({"limit": ["x"]}, "limit", 5) == 5


def test_get_qs_value_returns_default_when_missing():
    assert get_qs_value({"provider": ["google"]}, "provider") == "google"
    assert get_qs_value({}, "provider", default="azure") == "azure"


def test_get_payload_int_and_fallback():
    assert get_payload_int({"timeout_ms": "999"}, "timeout_ms", 100) == 999
    assert get_payload_int({"timeout_ms": "oops"}, "timeout_ms", 100) == 100


def test_get_qs_bool_variants():
    assert get_qs_bool({"force": ["1"]}, "force") is True
    assert get_qs_bool({"force": ["yes"]}, "force") is True
    assert get_qs_bool({"force": ["false"]}, "force") is False
    assert get_qs_bool({}, "force", default=True) is True
