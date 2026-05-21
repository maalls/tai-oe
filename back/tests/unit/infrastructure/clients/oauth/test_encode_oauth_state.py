from src.infrastructure.clients.oauth.state import decode_oauth_state, encode_oauth_state


def test_encode_oauth_state_roundtrip_payload():
    payload = {
        "redirect_url": "http://localhost:7153/settings",
        "callback_url": "http://localhost:7153/api/gmail/oauth/callback",
        "user_id": "user-123",
    }

    encoded = encode_oauth_state(payload)

    assert isinstance(encoded, str)
    assert decode_oauth_state(encoded) == payload
