from types import SimpleNamespace

from src.repository.token_repository import OAuthTokenRepository


class _SupabaseUpsertOAuthMock:
    def __init__(self, data):
        self.data = data
        self.payload = None
        self.on_conflict = None

    def table(self, _name):
        return self

    def upsert(self, payload, on_conflict=None):
        self.payload = payload
        self.on_conflict = on_conflict
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


def test_set_token_json_upserts_compound_key(monkeypatch):
    supabase = _SupabaseUpsertOAuthMock([{"user_id": "user-1"}])
    monkeypatch.setattr("src.repository.token_repository.get_supabase_service", lambda: supabase)

    repo = OAuthTokenRepository()

    ok = repo.set_token_json(
        user_id="user-1",
        provider="microsoft",
        service="mail",
        token_json="{}",
        scope="Mail.Read",
    )

    assert ok is True
    assert supabase.on_conflict == "user_id,provider,service"
    assert supabase.payload["user_id"] == "user-1"
    assert supabase.payload["provider"] == "microsoft"
    assert supabase.payload["service"] == "mail"
    assert supabase.payload["token_json"] == "{}"
    assert supabase.payload["scope"] == "Mail.Read"
    assert "updated_at" in supabase.payload


def test_set_token_json_converts_unix_expires_at(monkeypatch):
    supabase = _SupabaseUpsertOAuthMock([{"user_id": "user-1"}])
    monkeypatch.setattr("src.repository.token_repository.get_supabase_service", lambda: supabase)

    repo = OAuthTokenRepository()

    ok = repo.set_token_json(
        user_id="user-1",
        provider="microsoft",
        service="mail",
        token_json="{}",
        expires_at=1779442744,
    )

    assert ok is True
    assert isinstance(supabase.payload["expires_at"], str)
    assert "T" in supabase.payload["expires_at"]
