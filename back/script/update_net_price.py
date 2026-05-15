#!/usr/bin/env python3
"""
Script to update family entries net price information from a PDF file.
"""

import argparse
import sys
from pathlib import Path

from src.infrastructure.clients.llm import get_llm_service
from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.importers.net_price import NetPriceImporter


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update family entries net price information from a PDF file"
    )
    parser.add_argument(
        "brand_name",
        type=str,
        help="Name of the brand to update prices for"
    )
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file containing price information"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    # Verify PDF file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)
    
    if not pdf_path.is_file():
        print(f"Error: Path is not a file: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize clients
    try:
        supabase_client = get_supabase_service()
        llm_client = get_llm_service()
    except ImportError as e:
        print(f"Error: Failed to initialize clients: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Instantiate importer
    importer = NetPriceImporter(supabase_client, llm_client)
    print(f"Brand: {args.brand_name}")
    print(f"PDF file verified: {pdf_path}")
    print("Ready to process price updates...")

    importer.setBrand(args.brand_name)
    importer.load_pdf(pdf_path)
    summary = importer.run()

    print("Net price import summary:")
    print(f"- brand: {summary.get('brand_name')}")
    print(f"- parsed rows: {summary.get('parsed_rows', 0)}")
    print(f"- deleted existing net prices: {summary.get('deleted', 0)}")
    print(f"- created net prices: {summary.get('created', 0)}")
    print(f"- updated net prices: {summary.get('updated', 0)}")
    print("Price update process completed.")


if __name__ == "__main__":
    main()
