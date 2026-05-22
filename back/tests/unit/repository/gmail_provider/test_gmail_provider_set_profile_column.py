from src.repository.gmail_provider_repository import GmailProviderRepository


class _DbHandlerMock:
    def __init__(self, rows_affected=1):
        self.rows_affected = rows_affected
        self.calls = []

    def execute_update(self, query, params):
        self.calls.append((query, params))
        return self.rows_affected


def test_set_profile_column_updates_value():
    db_handler = _DbHandlerMock(rows_affected=1)
    repo = GmailProviderRepository(db_handler=db_handler)

    ok = repo._set_profile_column("user-1", "google_token_pickle", "{}")

    assert ok is True
    assert db_handler.calls == [
        (
            "UPDATE profile SET google_token_pickle = %s WHERE id = %s",
            ("{}", "user-1"),
        )
    ]
