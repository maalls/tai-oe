from src.service.email.email_auth_service import EmailAuthService


class _DbHandlerMock:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def execute_dict_query(self, query, params):
        self.calls.append((query, params))
        return self.rows


def test_get_sender_trust_info_returns_existing_sender():
    row = {
        "trust_score": 85,
        "is_verified": True,
        "is_trusted": True,
        "is_blocklisted": False,
        "total_emails_received": 12,
        "verified_emails_count": 11,
    }
    db_handler = _DbHandlerMock(rows=[row])
    service = EmailAuthService(db_handler=db_handler)

    result = service.get_sender_trust_info("user-1", "foo@example.com")

    assert result == row


def test_get_sender_trust_info_returns_default_when_missing():
    db_handler = _DbHandlerMock(rows=[])
    service = EmailAuthService(db_handler=db_handler)

    result = service.get_sender_trust_info("user-1", "foo@example.com")

    assert result["trust_score"] == 0
    assert result["is_verified"] is False
    assert result["is_trusted"] is False
    assert result["is_blocklisted"] is False
    assert result["total_emails_received"] == 0
    assert result["verified_emails_count"] == 0
