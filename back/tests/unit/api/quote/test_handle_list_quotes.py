"""Unit test for Quote.handle_list_quotes."""

from src.api.quote.handler import Quote


def test_handle_list_quotes_returns_sorted_quote_files(monkeypatch, tmp_path):
    assets_dir = tmp_path / "var" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "quote_20240101_aaa.pdf").write_bytes(b"a")
    (assets_dir / "quote_20240102_bbb.pdf").write_bytes(b"b")

    quote_handler = Quote.__new__(Quote)

    fake_file = assets_dir / "handler.py"
    fake_file.write_text("x", encoding="utf-8")
    monkeypatch.setattr("src.api.quote.handler.__file__", str(fake_file))

    result = quote_handler.handle_list_quotes()

    assert result["status"] == "ok"
    assert result["total"] == 2
    assert result["quotes"] == ["quote_20240102_bbb.pdf", "quote_20240101_aaa.pdf"]
