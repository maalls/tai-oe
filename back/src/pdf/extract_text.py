import argparse
import sys
from pathlib import Path

import pdfplumber


def extract_text(pdf_path: Path) -> str:
	texts = []
	with pdfplumber.open(str(pdf_path)) as pdf:
		for page in pdf.pages:
			try:
				texts.append(page.extract_text() or "")
			except Exception:
				continue
	return "\n\n".join(filter(None, texts)).strip()


def main() -> int:
	parser = argparse.ArgumentParser(description="Extract text from a PDF using pdfplumber")
	parser.add_argument("pdf", type=Path, help="Path to input PDF")
	args = parser.parse_args()

	if not args.pdf.exists():
		print(f"PDF not found: {args.pdf}", file=sys.stderr)
		return 1

	content = extract_text(args.pdf)
	if content:
		print(content)
		return 0
	print("No text extracted", file=sys.stderr)
	return 1


if __name__ == "__main__":
	sys.exit(main())
