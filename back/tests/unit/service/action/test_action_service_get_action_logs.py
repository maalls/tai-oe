"""Tests for ActionService.get_action_logs."""

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self):
        self.calls = []

    def get_execution_logs(self, action_id: str, limit: int = 50):
        self.calls.append((action_id, limit))
        return [{"action_id": action_id, "status": "ok"}]


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_get_action_logs_delegates_to_repository():
    repo = _ActionRepoStub()
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.get_action_logs("a-4", limit=25, user_id="u-1")

    assert result == [{"action_id": "a-4", "status": "ok"}]
    assert repo.calls == [("a-4", 25)]
