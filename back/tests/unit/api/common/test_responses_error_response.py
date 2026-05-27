from src.api.common.responses import error_response


def test_error_response_returns_standard_payload():
    response = error_response("boom", "ERR_CODE", status_code=409)

    assert response.status_code == 409
    body = response.body.decode("utf-8")
    assert '"status":"error"' in body
    assert '"error_code":"ERR_CODE"' in body
    assert '"message":"boom"' in body
