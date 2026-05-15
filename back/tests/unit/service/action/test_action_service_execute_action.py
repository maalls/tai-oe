"""Tests for ActionService.execute_action."""

from service.action.service import ActionService


class _ActionRepoStub:
    pass


class _SchedulerStub:
    def __init__(self):
        self.calls = []

    def execute_manually(self, action_id: str):
        self.calls.append(action_id)
        return {"action_id": action_id, "status": "success"}


def test_execute_action_delegates_to_scheduler():
    scheduler = _SchedulerStub()
    service = ActionService(action_repo=_ActionRepoStub(), scheduler=scheduler)

    result = service.execute_action("a-3", user_id="u-1")

    assert result == {"action_id": "a-3", "status": "success"}
    assert scheduler.calls == ["a-3"]
