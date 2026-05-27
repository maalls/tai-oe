import script.bootstrap_admin as bootstrap_admin


class _FakeDb:
    def __init__(self, user=None, admin_count=0, updated_user=None):
        self._user = user
        self._admin_count = admin_count
        self._updated_user = updated_user
        self.last_set_role_args = None

    def execute_dict_query(self, query, params=None):
        if "FROM profile WHERE lower(email)" in query:
            if self._user is None:
                return []
            return [self._user]

        if "COUNT(*) AS admin_count" in query:
            return [{"admin_count": self._admin_count}]

        raise AssertionError(f"Unexpected query: {query}")

    def set_user_role(self, user_id, role):
        self.last_set_role_args = (user_id, role)
        return self._updated_user


def test_bootstrap_admin_returns_error_when_user_not_found():
    db = _FakeDb(user=None, admin_count=0)
    messages = []

    exit_code = bootstrap_admin.bootstrap_admin(
        email="missing@example.com",
        db=db,
        out=messages.append,
    )

    assert exit_code == 1
    assert db.last_set_role_args is None
    assert any("User not found" in message for message in messages)


def test_bootstrap_admin_skips_when_user_already_admin():
    db = _FakeDb(
        user={"id": "u-1", "email": "admin@example.com", "role": "admin"},
        admin_count=1,
    )
    messages = []

    exit_code = bootstrap_admin.bootstrap_admin(
        email="admin@example.com",
        db=db,
        out=messages.append,
    )

    assert exit_code == 0
    assert db.last_set_role_args is None
    assert any("already admin" in message for message in messages)


def test_bootstrap_admin_requires_force_when_admin_exists():
    db = _FakeDb(
        user={"id": "u-2", "email": "user@example.com", "role": "user"},
        admin_count=1,
        updated_user={"id": "u-2", "email": "user@example.com", "role": "admin"},
    )
    messages = []

    exit_code = bootstrap_admin.bootstrap_admin(
        email="user@example.com",
        db=db,
        force=False,
        out=messages.append,
    )

    assert exit_code == 1
    assert db.last_set_role_args is None
    assert any("--force" in message for message in messages)


def test_bootstrap_admin_promotes_first_admin_without_force():
    db = _FakeDb(
        user={"id": "u-3", "email": "first@example.com", "role": "user"},
        admin_count=0,
        updated_user={"id": "u-3", "email": "first@example.com", "role": "admin"},
    )
    messages = []

    exit_code = bootstrap_admin.bootstrap_admin(
        email="first@example.com",
        db=db,
        force=False,
        out=messages.append,
    )

    assert exit_code == 0
    assert db.last_set_role_args == ("u-3", "admin")
    assert any("Bootstrap completed" in message for message in messages)


def test_bootstrap_admin_allows_force_when_admin_exists():
    db = _FakeDb(
        user={"id": "u-4", "email": "promote@example.com", "role": "user"},
        admin_count=2,
        updated_user={"id": "u-4", "email": "promote@example.com", "role": "admin"},
    )
    messages = []

    exit_code = bootstrap_admin.bootstrap_admin(
        email="promote@example.com",
        db=db,
        force=True,
        out=messages.append,
    )

    assert exit_code == 0
    assert db.last_set_role_args == ("u-4", "admin")
