"""Unit test for Quote.handle_get_quote_file."""

from src.api.quote.handler import Quote


def test_handle_get_quote_file_reads_from_storage(tmp_path):
    quote_handler = Quote.__new__(Quote)

    storage_path = tmp_path / "quote_abc.pdf"
    storage_path.write_bytes(b"pdf-content")

    quote_handler._get_storage_path = lambda source, filename: storage_path

    data = quote_handler.handle_get_quote_file("quote_abc.pdf")

    assert data == b"pdf-content"


def test_handle_get_quote_file_rejects_invalid_filename():
    quote_handler = Quote.__new__(Quote)
    quote_handler._get_storage_path = lambda source, filename: None

    try:
        quote_handler.handle_get_quote_file("../../etc/passwd")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        assert True
