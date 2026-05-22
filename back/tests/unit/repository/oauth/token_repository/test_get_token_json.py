from types import SimpleNamespace

from src.repository.token_repository import OAuthTokenRepository


class _DbHandlerMock:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return self.rows


def test_get_token_json_returns_stored_token(monkeypatch):
    db_handler = _DbHandlerMock([{"token_json": "{\"access_token\":\"abc\"}"}])
    repo = OAuthTokenRepository(db_handler=db_handler)

    token = repo.get_token_json("user-1", "microsoft", "mail")

    assert token == "{\"access_token\":\"abc\"}"
    assert db_handler.calls[0][1] == ("user-1", "microsoft", "mail")
