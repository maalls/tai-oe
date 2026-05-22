from src.command import email_cli


class _DbHandlerMock:
    def __init__(self, rows=None, should_fail=False):
        self.rows = rows or []
        self.should_fail = should_fail

    def execute_dict_query(self, query, params=None):
        if self.should_fail:
            raise RuntimeError("db failure")
        assert query == "SELECT id, email FROM profile"
        assert params is None
        return self.rows


def test_get_all_users_returns_rows(monkeypatch):
    monkeypatch.setattr(email_cli, "_DB_HANDLER", _DbHandlerMock(rows=[{"id": "u1", "email": "a@b.c"}]))

    users = email_cli.get_all_users()

    assert users == [{"id": "u1", "email": "a@b.c"}]


def test_get_all_users_returns_empty_on_error(monkeypatch):
    monkeypatch.setattr(email_cli, "_DB_HANDLER", _DbHandlerMock(should_fail=True))

    users = email_cli.get_all_users()

    assert users == []
