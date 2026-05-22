from src.repository.email_repository import EmailRepository


class _EmailDbHandlerMock:
    def __init__(self):
        self.calls = []

    def find_account_id_by_contact_email(self, email):
        self.calls.append(("find_account_id_by_contact_email", email))
        return None

    def create_account(self, name):
        self.calls.append(("create_account", name))
        return "account-1"

    def create_contact(self, name, email, account_id, phone=None, role_title=None):
        self.calls.append(("create_contact", name, email, account_id, phone, role_title))
        return "contact-1"

    def delete_account(self, account_id):
        self.calls.append(("delete_account", account_id))
        return True


def test_generate_account_from_email_creates_account_and_contact():
    repo = EmailRepository()
    repo.db_handler = _EmailDbHandlerMock()

    account_id = repo.generate_account_from_email({"from_email": "buyer@example.com", "from_name": "Buyer Co"})

    assert account_id == "account-1"
    assert repo.db_handler.calls == [
        ("find_account_id_by_contact_email", "buyer@example.com"),
        ("create_account", "Buyer Co"),
        ("create_contact", "Buyer Co", "buyer@example.com", "account-1", None, None),
    ]
