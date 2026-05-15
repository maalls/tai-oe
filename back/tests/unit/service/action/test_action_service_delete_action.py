"""Tests for ActionService.delete_action."""

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self, action):
        self.action = action
        self.deleted = []

    def get_action(self, action_id: str):
        return self.action

    def delete_action(self, action_id: str):
        self.deleted.append(action_id)


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_delete_action_returns_false_when_missing():
    repo = _ActionRepoStub(None)
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.delete_action("a-1", user_id="u-1")

    assert result is False
    assert repo.deleted == []


def test_delete_action_deletes_existing_action():
    repo = _ActionRepoStub({"id": "a-1"})
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.delete_action("a-1", user_id="u-1")

    assert result is True
    assert repo.deleted == ["a-1"]
