from pathlib import Path

from src.lib.extractors.rfp_source_picker import pick_best_rfp_source


def test_pick_best_rfp_source_uses_vision_for_pdf_when_enabled(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "rfq.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%fake")

    calls = {"vision": 0, "text": 0}

    def _fake_extract_rfp_from_text(_text, timeout_seconds=None):
        _ = timeout_seconds
        calls["text"] += 1
        return {"products": []}

    def _fake_extract_rfp_from_pdf_vision(_path, timeout_seconds=None):
        _ = timeout_seconds
        calls["vision"] += 1
        return {"products": [{"manufacturer": "ABB", "part_number": "123", "quantity": 2}]}

    monkeypatch.setenv("QUOTE_EXTRACTION_MODE", "vision")
    monkeypatch.setattr("src.lib.extractors.rfp_source_picker.extract_rfp_from_text", _fake_extract_rfp_from_text)
    monkeypatch.setattr(
        "src.lib.extractors.rfp_source_picker.extract_rfp_from_pdf_vision",
        _fake_extract_rfp_from_pdf_vision,
    )
    monkeypatch.setattr("src.lib.extractors.rfp_source_picker.extract_text", lambda _path: "pdf text")

    result = pick_best_rfp_source(
        body_text="",
        pdf_candidates=[{"id": "att-1", "filename": "rfq.pdf", "path": pdf_path}],
    )

    assert result["source"] == "pdf"
    assert result["product_count"] == 1
    assert calls["vision"] == 1
    assert calls["text"] == 0  # body is empty, no text extraction


def test_pick_best_rfp_source_falls_back_to_text_mode_on_invalid_env(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "rfq.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%fake")

    calls = {"vision": 0, "text": 0}

    def _fake_extract_rfp_from_text(_text, timeout_seconds=None):
        _ = timeout_seconds
        calls["text"] += 1
        return {"products": [{"manufacturer": "ABB", "part_number": "999", "quantity": 1}]}

    def _fake_extract_rfp_from_pdf_vision(_path, timeout_seconds=None):
        _ = timeout_seconds
        calls["vision"] += 1
        return {"products": [{"manufacturer": "ABB", "part_number": "123", "quantity": 2}]}

    monkeypatch.setenv("QUOTE_EXTRACTION_MODE", "oops")
    monkeypatch.setattr("src.lib.extractors.rfp_source_picker.extract_rfp_from_text", _fake_extract_rfp_from_text)
    monkeypatch.setattr(
        "src.lib.extractors.rfp_source_picker.extract_rfp_from_pdf_vision",
        _fake_extract_rfp_from_pdf_vision,
    )
    monkeypatch.setattr("src.lib.extractors.rfp_source_picker.extract_text", lambda _path: "pdf text")

    result = pick_best_rfp_source(
        body_text="",
        pdf_candidates=[{"id": "att-1", "filename": "rfq.pdf", "path": pdf_path}],
    )

    assert result["source"] == "pdf"
    assert result["product_count"] == 1
    assert calls["vision"] == 0
    assert calls["text"] == 1  # body is empty, only pdf text path
