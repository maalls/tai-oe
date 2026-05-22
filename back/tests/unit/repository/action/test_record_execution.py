from src.repository.action_repository import ActionRepository


class _DbHandlerMock:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def execute_dict_query(self, query, params=None):
        self.calls.append((query, params))
        if self.responses:
            return self.responses.pop(0)
        return []

    def execute_update(self, query, params=None):
        self.calls.append((query, params))
        return 1


def test_record_execution_inserts_log_and_completes_action_when_limit_reached():
    db_handler = _DbHandlerMock(
        [
            [{"id": "log-1"}],
            [{"id": "action-1", "execution_count": 1, "max_executions": 2, "schedule_type": "daily", "schedule_config": {}}],
            [{"id": "action-1", "execution_count": 2, "status": "completed"}],
        ]
    )
    repo = ActionRepository(db_handler=db_handler)

    log_row = repo.record_execution(
        action_id="action-1",
        status="success",
        duration_ms=123,
        result_data={"ok": True},
        error_message=None,
    )

    assert log_row == {"id": "log-1"}
    assert "INSERT INTO action_execution_log" in db_handler.calls[0][0]
    assert db_handler.calls[0][1][0] == "action-1"
    assert db_handler.calls[0][1][1] == "success"
    assert db_handler.calls[0][1][3] == 123
    assert db_handler.calls[0][1][4] == '{"ok": true}'
    assert db_handler.calls[1][0] == "SELECT * FROM action WHERE id = %s LIMIT 1"
    assert "UPDATE action SET" in db_handler.calls[2][0]
    assert db_handler.calls[2][1][-1] == "action-1"
