import script.list_random_products as list_random_products


def test_main_uses_injected_database_service(monkeypatch):
    captured = {"service_args": None, "handler_service": None, "query": None, "params": None}

    class _FakeHandler:
        def __init__(self, *, database_service):
            captured["handler_service"] = database_service

        def execute_dict_query(self, query, params):
            captured["query"] = query
            captured["params"] = params
            return []

    def _fake_create_database_service(*, current_file, require_postgres_password):
        captured["service_args"] = (current_file, require_postgres_password)
        return object()

    monkeypatch.setattr(list_random_products, "create_database_service", _fake_create_database_service)
    monkeypatch.setattr(list_random_products, "DatabaseHandler", _FakeHandler)
    monkeypatch.setattr(list_random_products, "_as_markdown", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        list_random_products.sys,
        "argv",
        [
            "list_random_products.py",
            "--count",
            "5",
            "--min-qty",
            "1",
            "--max-qty",
            "2",
            "--format",
            "markdown",
        ],
    )

    exit_code = list_random_products.main()

    assert exit_code == 0
    assert captured["service_args"][1] is True
    assert captured["handler_service"] is not None
    assert "SELECT" in captured["query"]
    assert captured["params"] == (5,)
