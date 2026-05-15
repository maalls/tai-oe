from pathlib import Path

from src.lib.extractors.pdf import extract_text


def test_extract_text_hello_world():
	pdf_path = Path(__file__).resolve().parents[4] / "fixtures" / "files" / "pdf" / "Hello_World.pdf"
	assert pdf_path.exists(), "Fixture PDF missing"

	content = extract_text(pdf_path)
	assert content.strip().lower() == "hello world!", "Extracted text does not match expected"
