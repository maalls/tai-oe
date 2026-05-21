from types import SimpleNamespace

from src.repository.email_repository import EmailRepository


class _SupabaseSelectMock:
    def __init__(self, data):
        self.data = data
        self.selected = None
        self.eq_filters = []

    def table(self, _name):
        return self

    def select(self, column):
        self.selected = column
        return self

    def eq(self, key, value):
        self.eq_filters.append((key, value))
        return self

    def limit(self, _value):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


def test_get_profile_column_returns_value(monkeypatch):
    supabase = _SupabaseSelectMock([{"google_token_pickle": "abc123"}])
    monkeypatch.setattr("src.repository.email_repository.get_supabase_service", lambda: supabase)

    repo = EmailRepository()

    value = repo._get_profile_column("user-1", "google_token_pickle")

    assert value == "abc123"
    assert supabase.selected == "google_token_pickle"
    assert supabase.eq_filters == [("id", "user-1")]
