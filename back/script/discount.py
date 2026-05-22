#!/usr/bin/env python3
"""Inspect discount PDF documents through the DiscountImporter."""

import argparse
import json
import sys
from pathlib import Path

from src.infrastructure.clients.llm import get_llm_service
from src.infrastructure.runtime.env_loader import load_runtime_env
from src.lib.importers.discount import DiscountImporter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect discount PDF files using the DiscountImporter"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pdf_parser = subparsers.add_parser(
        "pdf", help="Dump extracted PDF text returned by load_pdf"
    )
    pdf_parser.add_argument("pdf_file", type=str, help="Path to the input PDF file")

    parse_parser = subparsers.add_parser(
        "parse", help="Dump JSON returned by parseDiscounts"
    )
    parse_parser.add_argument("pdf_file", type=str, help="Path to the input PDF file")

    vision_parser = subparsers.add_parser(
        "vision", help="Dump JSON returned by parseDiscountsUsingVision"
    )
    vision_parser.add_argument("pdf_file", type=str, help="Path to the input PDF file")

    return parser.parse_args()


def _validate_pdf_path(pdf_file: str) -> Path:
    pdf_path = Path(pdf_file)
    if not pdf_path.exists() or not pdf_path.is_file():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    return pdf_path


def main() -> None:
    args = parse_args()
    pdf_path = _validate_pdf_path(args.pdf_file)

    if args.command == "pdf":
        importer = DiscountImporter(supabase_client=object(), llm_client=object())
        print(importer.load_pdf(pdf_path))
        return

    load_runtime_env(current_file=__file__)

    try:
        llm_client = get_llm_service()
    except ImportError as exc:
        print(f"Error: failed to initialize LLM client: {exc}", file=sys.stderr)
        sys.exit(1)

    importer = DiscountImporter(supabase_client=object(), llm_client=llm_client)

    if args.command == "parse":
        importer.load_pdf(pdf_path)
        print(json.dumps(importer.parseDiscounts(), ensure_ascii=False, indent=2))
        return

    print(json.dumps(importer.parseDiscountsUsingVision(pdf_path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()