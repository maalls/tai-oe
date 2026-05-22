from types import SimpleNamespace

from src.repository.token_repository import OAuthTokenRepository


class _DbHandlerMock:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return self.rows


def test_set_token_json_upserts_compound_key(monkeypatch):
    db_handler = _DbHandlerMock([{"user_id": "user-1"}])
    repo = OAuthTokenRepository(db_handler=db_handler)

    ok = repo.set_token_json(
        user_id="user-1",
        provider="microsoft",
        service="mail",
        token_json="{}",
        scope="Mail.Read",
    )

    assert ok is True
    assert db_handler.calls[0][1][0:4] == ("user-1", "microsoft", "mail", "{}")
    assert db_handler.calls[0][1][4] == "Mail.Read"
    assert "T" in db_handler.calls[0][1][6]


def test_set_token_json_converts_unix_expires_at(monkeypatch):
    db_handler = _DbHandlerMock([{"user_id": "user-1"}])
    repo = OAuthTokenRepository(db_handler=db_handler)

    ok = repo.set_token_json(
        user_id="user-1",
        provider="microsoft",
        service="mail",
        token_json="{}",
        expires_at=1779442744,
    )

    assert ok is True
    assert isinstance(db_handler.calls[0][1][5], str)
    assert "T" in db_handler.calls[0][1][5]
