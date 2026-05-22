from src.repository.action_repository import ActionRepository


class _DbHandlerMock:
    def __init__(self):
        self.calls = []

    def execute_update(self, query, params=None):
        self.calls.append((query, params))
        return 1


def test_delete_action_executes_delete_statement():
    db_handler = _DbHandlerMock()
    repo = ActionRepository(db_handler=db_handler)

    deleted = repo.delete_action("action-1")

    assert deleted is True
    assert db_handler.calls[0][0] == "DELETE FROM action WHERE id = %s"
    assert db_handler.calls[0][1] == ("action-1",)
