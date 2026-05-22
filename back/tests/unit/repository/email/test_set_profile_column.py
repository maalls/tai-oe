from src.repository.email_repository import EmailRepository


class _EmailDbHandlerMock:
    def __init__(self):
        self.calls = []

    def set_profile_column(self, user_id, column, value):
        self.calls.append((user_id, column, value))
        return True


def test_set_profile_column_updates_value():
    db_handler = _EmailDbHandlerMock()
    repo = EmailRepository()
    repo.db_handler = db_handler

    ok = repo._set_profile_column("user-1", "outlook_token_json", "{}")

    assert ok is True
    assert db_handler.calls == [("user-1", "outlook_token_json", "{}")]
