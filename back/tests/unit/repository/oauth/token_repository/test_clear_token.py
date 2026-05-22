from types import SimpleNamespace

from src.repository.token_repository import OAuthTokenRepository


class _DbHandlerMock:
    def __init__(self):
        self.calls = []

    def execute_update(self, query, params=None):
        self.calls.append((query, params))
        return 1


def test_clear_token_deletes_by_compound_key(monkeypatch):
    db_handler = _DbHandlerMock()
    repo = OAuthTokenRepository(db_handler=db_handler)

    ok = repo.clear_token("user-1", "microsoft", "mail")

    assert ok is True
    assert db_handler.calls[0][1] == ("user-1", "microsoft", "mail")
