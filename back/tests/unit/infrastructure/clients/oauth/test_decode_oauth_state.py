from src.infrastructure.clients.oauth.state import decode_oauth_state


def test_decode_oauth_state_returns_empty_dict_on_invalid_input():
    assert decode_oauth_state("not-a-valid-state") == {}
