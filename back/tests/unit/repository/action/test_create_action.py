from src.repository.action_repository import ActionRepository


class _DbHandlerMock:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return self.rows


def test_create_action_inserts_row_with_serialized_configs():
    db_handler = _DbHandlerMock([{"id": "action-1", "status": "active"}])
    repo = ActionRepository(db_handler=db_handler)

    action = repo.create_action(
        user_id="user-1",
        opportunity_id="opp-1",
        action_type="follow_up_email",
        schedule_type="daily",
        schedule_config={"time": "09:00"},
        config={"template": "default"},
        max_executions=3,
    )

    assert action == {"id": "action-1", "status": "active"}
    assert "INSERT INTO action" in db_handler.calls[0][0]
    assert db_handler.calls[0][1][0:4] == ("user-1", "opp-1", "follow_up_email", "daily")
    assert db_handler.calls[0][1][4] == '{"time": "09:00"}'
    assert db_handler.calls[0][1][5] == '{"template": "default"}'
    assert db_handler.calls[0][1][7] == 3
    assert db_handler.calls[0][1][8] == "user-1"
