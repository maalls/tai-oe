"""Tests for ActionService.get_action."""

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self, action):
        self.action = action
        self.calls = []

    def get_action(self, action_id: str):
        self.calls.append(action_id)
        return self.action


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_get_action_returns_repository_value():
    repo = _ActionRepoStub({"id": "a-1"})
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.get_action("a-1", user_id="u-1")

    assert result == {"id": "a-1"}
    assert repo.calls == ["a-1"]
