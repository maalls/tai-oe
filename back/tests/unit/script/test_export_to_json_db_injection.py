import script.exportToJson as export_to_json


def test_export_table_to_json_uses_injected_database_service(monkeypatch, tmp_path):
    captured = {"service_args": None, "handler_service": None, "query": None}

    class _FakeHandler:
        def __init__(self, *, database_service):
            captured["handler_service"] = database_service

        def execute_dict_query(self, query):
            captured["query"] = query
            return [{"id": 1, "name": "demo"}]

    def _fake_create_database_service(*, current_file, require_postgres_password):
        captured["service_args"] = (current_file, require_postgres_password)
        return object()

    monkeypatch.setattr(export_to_json, "create_database_service", _fake_create_database_service)
    monkeypatch.setattr(export_to_json, "DatabaseHandler", _FakeHandler)

    output_file = tmp_path / "out.json"

    export_to_json.export_table_to_json(
        table="profile",
        output_file=str(output_file),
        where_clause="id = 1",
        limit=1,
    )

    assert captured["service_args"][1] is True
    assert captured["handler_service"] is not None
    assert "SELECT" in captured["query"]
    assert output_file.exists()
