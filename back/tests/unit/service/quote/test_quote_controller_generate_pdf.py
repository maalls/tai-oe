"""Tests for QuoteController PDF generation path resolution."""

from pathlib import Path

from src.service.quote.quote_controller import QuoteController


class _Template:
    def __init__(self, recorder):
        self.recorder = recorder

    def render(self, **_kwargs):
        self.recorder["render_called"] = True
        return "<html><body>ok</body></html>"


class _Environment:
    def __init__(self, loader, recorder):
        self.loader = loader
        self.filters = {}
        self.recorder = recorder

    def get_template(self, template_name):
        self.recorder["template_name"] = template_name
        return _Template(self.recorder)


class _Loader:
    def __init__(self, path, recorder):
        self.path = path
        recorder["templates_path"] = path


class _Html:
    def __init__(self, string):
        self.string = string

    def write_pdf(self, output_path):
        Path(output_path).write_bytes(b"PDF")


def test_generate_quote_pdf_uses_back_templates_dir(monkeypatch, tmp_path):
    recorder = {}

    monkeypatch.setattr(QuoteController, "_get_storage_dir", staticmethod(lambda _source: tmp_path))
    monkeypatch.setattr(
        "src.service.quote.quote_controller.FileSystemLoader",
        lambda path: _Loader(path, recorder),
    )
    monkeypatch.setattr(
        "src.service.quote.quote_controller.Environment",
        lambda loader: _Environment(loader, recorder),
    )
    monkeypatch.setattr("src.service.quote.quote_controller.HTML", _Html)

    controller = QuoteController()
    filename = controller._generate_quote_pdf(
        {
            "quote_id": "Q-1",
            "currency": "EUR",
            "account": {},
            "contact": {},
            "products": [],
            "totals": {},
        }
    )

    expected_templates_dir = Path(__file__).resolve().parents[4] / "templates"

    assert recorder["template_name"] == "quote.html"
    assert recorder["render_called"] is True
    assert Path(recorder["templates_path"]).resolve() == expected_templates_dir.resolve()
    assert (tmp_path / filename).exists()
