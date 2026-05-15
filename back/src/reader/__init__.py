"""Backward-compatible shim — real implementation in src.lib.readers."""
from src.lib.readers.csv import CSVReader
from src.lib.readers.xls import XlsReader
__all__ = ["CSVReader", "XlsReader"]
