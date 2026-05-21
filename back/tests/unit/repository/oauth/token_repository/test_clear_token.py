from types import SimpleNamespace

from src.repository.oauth.token_repository import OAuthTokenRepository


class _SupabaseDeleteOAuthMock:
    def __init__(self):
        self.eq_filters = []

    def table(self, _name):
        return self

    def delete(self):
        return self

    def eq(self, key, value):
        self.eq_filters.append((key, value))
        return self

    def execute(self):
        return SimpleNamespace(data=[])


def test_clear_token_deletes_by_compound_key(monkeypatch):
    supabase = _SupabaseDeleteOAuthMock()
    monkeypatch.setattr("src.repository.oauth.token_repository.get_supabase_service", lambda: supabase)

    repo = OAuthTokenRepository()

    ok = repo.clear_token("user-1", "microsoft", "mail")

    assert ok is True
    assert supabase.eq_filters == [
        ("user_id", "user-1"),
        ("provider", "microsoft"),
        ("service", "mail"),
    ]
