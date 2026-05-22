from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.infrastructure.config import create_database_handler
from src.infrastructure.database.supabase_compat_adapter import SupabaseCompatAdapter
from src.lib.importers.fabdis import FabdisImporter


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Import Fabdis Excel data (products, media, etc)."
	)
	parser.add_argument("fabdis_file", type=Path, help="Path to the Fabdis Excel file")
	parser.add_argument(
		"--media-only",
		action="store_true",
		help="Only import product media (skip products, brands, etc)",
	)
	return parser.parse_args()


def main() -> int:
	args = parse_args()

	try:
		db_handler = create_database_handler(
			current_file=__file__,
			require_postgres_password=False,
		)
		supabase_client = SupabaseCompatAdapter(db_handler)
	except Exception as exc:
		print(f"Error: could not initialize database handler: {exc}")
		return 1

	importer = FabdisImporter(pd, supabase_client)

	try:
		importer.load(args.fabdis_file)
		if args.media_only:
			media_stats = importer.import_media(return_stats=True)
			print("FABDIS import summary (media only)")
			print(
				f"- product-media: {media_stats['created']} created, {media_stats['existing']} existing, {media_stats['skipped']} ignored (missing product)"
			)
		else:
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
			print(f"- families created: {summary.get('families_created', 0)}")
			print(
				f"- product-family links created: {summary.get('product_family_created', 0)}"
			)
			print(
				f"- product-media: {summary.get('media_upserted', 0)} created, {summary.get('media_existing', 0)} existing, {summary.get('media_skipped', 0)} ignored (missing product)"
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
