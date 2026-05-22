"""Tests for QuoteService PDF generation path resolution."""

from pathlib import Path

from src.service.quote.service import QuoteService


class _Template:
    def __init__(self, recorder):
        self.recorder = recorder

    def render(self, **kwargs):
        self.recorder["render_kwargs"] = kwargs
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

    monkeypatch.setattr(QuoteService, "_get_storage_dir", staticmethod(lambda _source: tmp_path))
    monkeypatch.setattr(
        "src.service.quote.service.FileSystemLoader",
        lambda path: _Loader(path, recorder),
    )
    monkeypatch.setattr(
        "src.service.quote.service.Environment",
        lambda loader: _Environment(loader, recorder),
    )
    monkeypatch.setattr("src.service.quote.service.HTML", _Html)

    controller = QuoteService()
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


def test_generate_quote_pdf_computes_unit_price_and_line_total(monkeypatch, tmp_path):
    recorder = {}

    monkeypatch.setattr(QuoteService, "_get_storage_dir", staticmethod(lambda _source: tmp_path))
    monkeypatch.setattr(
        "src.service.quote.service.FileSystemLoader",
        lambda path: _Loader(path, recorder),
    )
    monkeypatch.setattr(
        "src.service.quote.service.Environment",
        lambda loader: _Environment(loader, recorder),
    )
    monkeypatch.setattr("src.service.quote.service.HTML", _Html)

    controller = QuoteService()
    controller._generate_quote_pdf(
        {
            "quote_id": "Q-2",
            "currency": "EUR",
            "account": {},
            "contact": {},
            "products": [
                {
                    "quantity": 2,
                    "unit_price": 15.0,
                    "client_discount_rate": 10,
                }
            ],
            "totals": {"subtotal": 27.0, "tax": 5.4, "total": 32.4},
        }
    )

    products = recorder["render_kwargs"]["products"]
    assert products[0]["unit_price"] == 13.5
    assert products[0]["line_total"] == 27.0
