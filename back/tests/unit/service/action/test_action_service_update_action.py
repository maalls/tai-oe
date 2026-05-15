"""Tests for ActionService.update_action."""

from service.action.service import ActionService


class _ActionRepoStub:
    def __init__(self, action):
        self.action = action
        self.updated_calls = []

    def get_action(self, action_id: str):
        return self.action

    def update_action(self, action_id: str, data):
        self.updated_calls.append((action_id, data))
        return {"id": action_id, **data}


class _SchedulerStub:
    def execute_manually(self, action_id: str):
        return {"action_id": action_id, "status": "ok"}


def test_update_action_returns_none_when_not_found():
    repo = _ActionRepoStub(None)
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.update_action("a-1", {"status": "paused"}, user_id="u-1")

    assert result is None
    assert repo.updated_calls == []


def test_update_action_updates_existing_action():
    repo = _ActionRepoStub({"id": "a-1", "status": "active"})
    service = ActionService(action_repo=repo, scheduler=_SchedulerStub())

    result = service.update_action("a-1", {"status": "paused"}, user_id="u-1")

    assert result == {"id": "a-1", "status": "paused"}
    assert repo.updated_calls == [("a-1", {"status": "paused"})]
