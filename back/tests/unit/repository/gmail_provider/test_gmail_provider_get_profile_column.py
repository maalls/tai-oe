from src.repository.gmail_provider_repository import GmailProviderRepository


class _DbHandlerMock:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_dict_query(self, query, params):
        self.calls.append((query, params))
        return self.rows


def test_get_profile_column_returns_value():
    db_handler = _DbHandlerMock(rows=[{"google_token_pickle": "abc123"}])
    repo = GmailProviderRepository(db_handler=db_handler)

    value = repo._get_profile_column("user-1", "google_token_pickle")

    assert value == "abc123"
    assert db_handler.calls == [
        (
            "SELECT google_token_pickle FROM profile WHERE id = %s LIMIT 1",
            ("user-1",),
        )
    ]
