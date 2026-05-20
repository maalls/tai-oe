from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.importers.fabdis import FabdisImporter


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Read a Fabdis Excel file and print its sheet names."
	)
	parser.add_argument("fabdis_file", type=Path, help="Path to the Fabdis Excel file")
	return parser.parse_args()


def main() -> int:
	args = parse_args()

	try:
		supabase_client = get_supabase_service()
	except ValueError as exc:
		print(f"Error: could not initialize Supabase client: {exc}")
		return 1

	importer = FabdisImporter(pd, supabase_client)

	try:
		importer.load(args.fabdis_file)
		importer.run()
		summary = importer.last_summary
		print("FABDIS import summary")
		print(f"- cartouche rows: {summary['cartouche_rows']}")
		print(
			f"- vendors: {summary['vendors_in_file']} total ({summary['vendors_created']} created, {summary['vendors_existing']} existing)"
		)
		print(
			f"- brands: {summary['brands_in_file']} total ({summary['brands_created']} created, {summary['brands_existing']} existing)"
		)
		print(
			f"- products: {summary.get('products_in_file', 0)} total ({summary.get('products_created', 0)} created, {summary.get('products_existing', 0)} existing)"
		)
		print(
			f"- families created: {summary.get('families_created', 0)}"
		)
		print(
			f"- product-family links created: {summary.get('product_family_created', 0)}"
		)
	except FileNotFoundError as exc:
		print(f"Error: {exc}")
		return 1
	except ValueError as exc:
		print(f"Error: could not read Excel file: {exc}")
		return 1
	except ImportError as exc:
		print(f"Error: missing dependency to read this Excel file: {exc}")
		return 1

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
