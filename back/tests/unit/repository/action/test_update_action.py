from src.repository.action_repository import ActionRepository


class _DbHandlerMock:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        return self.rows


def test_update_action_serializes_json_fields_and_sets_updated_at():
    db_handler = _DbHandlerMock([{"id": "action-1", "status": "paused"}])
    repo = ActionRepository(db_handler=db_handler)

    action = repo.update_action(
        "action-1",
        {
            "status": "paused",
            "schedule_config": {"time": "10:00"},
        },
    )

    assert action == {"id": "action-1", "status": "paused"}
    assert "UPDATE action SET" in db_handler.calls[0][0]
    assert db_handler.calls[0][1][0] == "paused"
    assert db_handler.calls[0][1][1] == '{"time": "10:00"}'
    assert db_handler.calls[0][1][-1] == "action-1"
