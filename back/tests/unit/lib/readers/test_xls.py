import sys
from pathlib import Path

from src.reader.xls import XlsReader


def test_convert_to_csv_creates_expected_files(tmp_path: Path):
	assets_dir = Path(__file__).resolve().parent / "assets"

	# Prefer .xlsx asset (present in repo) but fall back to .xls if provided later
	input_file = assets_dir / "dummy.xlsx"
	if not input_file.exists():
		input_file = assets_dir / "dummy.xls"

	assert input_file.exists(), "Test asset dummy.xlsx/.xls is missing"

	output_dir = tmp_path / "output"
	XlsReader.convertToCsv(input_file, output_dir)

	csv_files = {p.name for p in output_dir.glob("*.csv")}

	assert csv_files == {"hello.csv", "world.csv"}
	assert len(csv_files) == 2
