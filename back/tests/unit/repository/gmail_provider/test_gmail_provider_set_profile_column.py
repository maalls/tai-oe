import base64
import pickle

from src.repository.gmail_provider_repository import GmailProviderRepository


class _EmailDbHandlerMock:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def set_profile_column(self, user_id, column, value):
        self.calls.append((user_id, column, value))
        return self.result

    def clear_profile_column(self, user_id, column):
        self.calls.append(("clear", user_id, column))
        return self.result


def test_save_profile_token_updates_value():
    email_db_handler = _EmailDbHandlerMock(result=True)
    repo = GmailProviderRepository(email_db_handler=email_db_handler)
    creds = {"token": "abc"}

    ok = repo._save_profile_token("user-1", creds)

    assert ok is True
    expected_token = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
    assert email_db_handler.calls == [("user-1", "google_token_pickle", expected_token)]


def test_clear_profile_token_clears_value():
    email_db_handler = _EmailDbHandlerMock(result=True)
    repo = GmailProviderRepository(email_db_handler=email_db_handler)

    ok = repo._clear_profile_token("user-1")

    assert ok is True
    assert email_db_handler.calls == [("clear", "user-1", "google_token_pickle")]
