from types import SimpleNamespace

from src.repository.oauth.token_repository import OAuthTokenRepository


class _SupabaseSelectOAuthMock:
    def __init__(self, data):
        self.data = data
        self.eq_filters = []

    def table(self, _name):
        return self

    def select(self, _columns):
        return self

    def eq(self, key, value):
        self.eq_filters.append((key, value))
        return self

    def limit(self, _value):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


def test_get_token_json_returns_stored_token(monkeypatch):
    supabase = _SupabaseSelectOAuthMock([{"token_json": "{\"access_token\":\"abc\"}"}])
    monkeypatch.setattr("src.repository.oauth.token_repository.get_supabase_service", lambda: supabase)

    repo = OAuthTokenRepository()

    token = repo.get_token_json("user-1", "microsoft", "mail")

    assert token == "{\"access_token\":\"abc\"}"
    assert supabase.eq_filters == [
        ("user_id", "user-1"),
        ("provider", "microsoft"),
        ("service", "mail"),
    ]
