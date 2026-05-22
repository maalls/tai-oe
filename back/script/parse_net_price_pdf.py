#!/usr/bin/env python3
"""Parse net price table from a PDF using the NetPriceImporter."""

import argparse
import json
import sys
from pathlib import Path

from src.infrastructure.clients.llm import get_llm_service
from src.infrastructure.runtime.env_loader import load_runtime_env
from src.lib.importers.net_price import NetPriceImporter


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Parse product net prices from a PDF and print LLM extraction JSON"
	)
	parser.add_argument("pdf_file", type=str, help="Path to the input PDF file")
	return parser.parse_args()


def main() -> None:
	load_runtime_env(current_file=__file__)

	args = parse_args()
	pdf_path = Path(args.pdf_file)

	if not pdf_path.exists() or not pdf_path.is_file():
		print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
		sys.exit(1)

	try:
		llm_client = get_llm_service()
	except ImportError as exc:
		print(f"Error: failed to initialize LLM client: {exc}", file=sys.stderr)
		sys.exit(1)

	importer = NetPriceImporter(supabase_client=object(), llm_client=llm_client)
	importer.load_pdf(pdf_path)
	rows = importer.parseNetPrices()

	print(json.dumps({"products": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()
