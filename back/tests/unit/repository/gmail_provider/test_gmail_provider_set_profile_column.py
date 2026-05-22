from src.repository.gmail_provider_repository import GmailProviderRepository


class _EmailDbHandlerMock:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def set_profile_column(self, user_id, column, value):
        self.calls.append((user_id, column, value))
        return self.result


def test_set_profile_column_updates_value():
    email_db_handler = _EmailDbHandlerMock(result=True)
    repo = GmailProviderRepository(email_db_handler=email_db_handler)

    ok = repo._set_profile_column("user-1", "google_token_pickle", "{}")

    assert ok is True
    assert email_db_handler.calls == [("user-1", "google_token_pickle", "{}")]
