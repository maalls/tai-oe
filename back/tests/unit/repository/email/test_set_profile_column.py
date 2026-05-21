from types import SimpleNamespace

from src.repository.email_repository import EmailRepository


class _SupabaseUpdateMock:
    def __init__(self, data):
        self.data = data
        self.updated = None
        self.eq_filters = []

    def table(self, _name):
        return self

    def update(self, payload):
        self.updated = payload
        return self

    def eq(self, key, value):
        self.eq_filters.append((key, value))
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


def test_set_profile_column_updates_value(monkeypatch):
    supabase = _SupabaseUpdateMock([{"id": "user-1"}])
    monkeypatch.setattr("src.repository.email_repository.get_supabase_service", lambda: supabase)

    repo = EmailRepository()

    ok = repo._set_profile_column("user-1", "outlook_token_json", "{}")

    assert ok is True
    assert supabase.updated == {"outlook_token_json": "{}"}
    assert supabase.eq_filters == [("id", "user-1")]
