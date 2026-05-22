from src.service.email.email_auth_service import EmailAuthService


class _DbHandlerMock:
    def __init__(self, select_rows=None, insert_rows=None):
        self.select_rows = select_rows or []
        self.insert_rows = insert_rows or []
        self.select_calls = []
        self.update_calls = []

    def execute_dict_query(self, query, params):
        self.select_calls.append((query, params))
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("select * from sender_verification"):
            return self.select_rows
        if normalized.startswith("insert into sender_verification"):
            return self.insert_rows
        if normalized.startswith("update sender_verification"):
            return [{"id": "sv-1"}]
        return []

    def execute_update(self, query, params):
        self.update_calls.append((query, params))
        return 1


def test_verify_sender_creates_sender_verification():
    db_handler = _DbHandlerMock(select_rows=[], insert_rows=[{"id": "sv-new"}])
    service = EmailAuthService(db_handler=db_handler)

    result = service.verify_sender(
        user_id="user-1",
        sender_email="foo@example.com",
        sender_name="Foo",
        auth_score=80,
        is_verified=True,
        spf_status="PASS",
        dkim_status="PASS",
        dmarc_status="PASS",
    )

    assert result["status"] == "created"
    assert result["sender_email"] == "foo@example.com"
    assert result["trust_score"] == 80
    assert result["is_verified"] is True


def test_verify_sender_updates_existing_sender_verification():
    existing = {
        "id": "sv-1",
        "auth_history": [{"score": 40}, {"score": 60}],
        "total_emails_received": 2,
        "verified_emails_count": 1,
    }
    db_handler = _DbHandlerMock(select_rows=[existing])
    service = EmailAuthService(db_handler=db_handler)

    result = service.verify_sender(
        user_id="user-1",
        sender_email="foo@example.com",
        sender_name="Foo",
        auth_score=80,
        is_verified=True,
        spf_status="PASS",
        dkim_status="PASS",
        dmarc_status="PASS",
    )

    assert result["status"] == "updated"
    assert result["sender_email"] == "foo@example.com"
    assert result["trust_score"] == 60
    assert result["is_verified"] is True
