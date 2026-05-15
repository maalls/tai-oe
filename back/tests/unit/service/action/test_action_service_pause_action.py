"""Tests for ActionService.pause_action."""

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self):
        self.calls = []

    def pause_action(self, action_id: str):
        self.calls.append(action_id)
        return {"id": action_id, "status": "paused"}


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_pause_action_delegates_to_repository():
    repo = _ActionRepoStub()
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.pause_action("a-2", user_id="u-1")

    assert result == {"id": "a-2", "status": "paused"}
    assert repo.calls == ["a-2"]
