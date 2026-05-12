#!/usr/bin/env python3
"""
Script to update family discount information from a PDF file.
"""

import argparse
import sys
from pathlib import Path

from src.discount.importer import DiscountImporter
from src.llm import get_llm_service
from src.supabase import get_supabase_service


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update family discount information from a PDF file"
    )
    parser.add_argument(
        "brand_name",
        type=str,
        help="Name of the brand to update discounts for",
    )
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file containing discount information",
    )
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip rows that do not match a family by code or description",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)

    if not pdf_path.is_file():
        print(f"Error: Path is not a file: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)

    try:
        supabase_client = get_supabase_service()
        llm_client = get_llm_service()
    except ImportError as exc:
        print(f"Error: Failed to initialize clients: {exc}", file=sys.stderr)
        sys.exit(1)

    importer = DiscountImporter(supabase_client, llm_client)
    print(f"Brand: {args.brand_name}")
    print(f"PDF file verified: {pdf_path}")
    print("Ready to process discount updates...")

    importer.setBrand(args.brand_name)
    importer.load_pdf(pdf_path)
    summary = importer.run(skip_missing=args.skip_missing)

    print("Discount import summary:")
    print(f"- brand: {summary.get('brand_name')}")
    print(f"- parsed rows: {summary.get('parsed_rows', 0)}")
    print(f"- updated: {summary.get('updated', 0)}")
    print(f"- skipped: {summary.get('skipped', 0)}")

    skipped_rows = summary.get("skipped_rows") or []
    if skipped_rows:
        print("- skipped rows detail:")
        for item in skipped_rows:
            print(
                f"  - row {item.get('row')}: code={item.get('family_code')!r}, "
                f"description={item.get('description')!r}"
            )

    print("Discount update process completed.")


if __name__ == "__main__":
    main()