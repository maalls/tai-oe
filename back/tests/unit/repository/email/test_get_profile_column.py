from src.repository.email_repository import EmailRepository


class _EmailDbHandlerMock:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def get_profile_column(self, user_id, column):
        self.calls.append((user_id, column))
        return self.row.get(column)


def test_get_profile_column_returns_value():
    db_handler = _EmailDbHandlerMock({"google_token_pickle": "abc123"})
    repo = EmailRepository()
    repo.db_handler = db_handler

    value = repo._get_profile_column("user-1", "google_token_pickle")

    assert value == "abc123"
    assert db_handler.calls == [("user-1", "google_token_pickle")]
