from src.repository.gmail_provider_repository import GmailProviderRepository


class _EmailDbHandlerMock:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def get_profile_column(self, user_id, column):
        self.calls.append((user_id, column))
        return self.value


def test_get_profile_column_returns_value():
    email_db_handler = _EmailDbHandlerMock(value="abc123")
    repo = GmailProviderRepository(email_db_handler=email_db_handler)

    value = repo._get_profile_column("user-1", "google_token_pickle")

    assert value == "abc123"
    assert email_db_handler.calls == [("user-1", "google_token_pickle")]
