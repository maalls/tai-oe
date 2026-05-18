import pytest
from pydantic import ValidationError

from src.api_fastapi.auth.schemas import LoginRequest, OAuthCallbackQuery, OAuthLoginQuery, SignupRequest


def test_signup_request_accepts_valid_payload():
    payload = SignupRequest(email=" user@example.com ", password="secret")

    assert payload.email == "user@example.com"
    assert payload.password == "secret"


def test_signup_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        SignupRequest(email="invalid", password="secret")


def test_login_request_rejects_empty_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")


def test_oauth_login_query_requires_provider():
    with pytest.raises(ValidationError):
        OAuthLoginQuery(provider="", redirect_url="https://example.com")


def test_oauth_callback_query_requires_provider_and_code():
    with pytest.raises(ValidationError):
        OAuthCallbackQuery(provider="google", code="")
