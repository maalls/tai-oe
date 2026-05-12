from pathlib import Path

from src.pdf.extract_text import extract_text


def test_extract_text_hello_world():
	pdf_path = Path(__file__).parent / "Hello_World.pdf"
	assert pdf_path.exists(), "Fixture PDF missing"

	content = extract_text(pdf_path)
	assert content.strip().lower() == "hello world!", "Extracted text does not match expected"
