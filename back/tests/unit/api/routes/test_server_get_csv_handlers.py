from src.api.routes.server_get_csv_handlers import (
    handle_csv_get,
    handle_csv_search_get,
)


class _RequestHandlersStub:
    def handle_list_files(self, qs):
        return [qs]

    def handle_search(self, qs, embedding_generator):
        return {"qs": qs, "embedding": embedding_generator}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def get_embedding_generator(self):
        return "emb"

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status

    def _handle_raw_stream(self, qs, request_handlers):
        return ("raw", qs, request_handlers)

    def _handle_source_stream(self, qs, request_handlers):
        return ("source", qs, request_handlers)

    def _handle_csv_download(self, qs, request_handlers):
        return ("download", qs, request_handlers)


def test_handle_csv_get_files_path_delegates_to_list_files():
    handler = _HandlerStub()

    result = handle_csv_get(handler, "/api/csv/files", {"a": ["1"]})

    assert result == ([{"a": ["1"]}], 200)


def test_handle_csv_search_get_uses_embedding_generator():
    handler = _HandlerStub()

    result = handle_csv_search_get(handler, {"q": ["x"]}, handler.get_request_handlers())

    assert result == ({"qs": {"q": ["x"]}, "embedding": "emb"}, 200)
