"""Fabdis vendor handling utilities."""

from __future__ import annotations

from pathlib import Path
import csv
import os
import random
from typing import Any, Dict, List
import json
import psycopg2

from product import handle_product
from brand import handle_brand


def handle_vendor(config: Dict[str, Any]) -> None:
	con = get_db_connection()
	vendor = generate_vendor(config, con)
	file = get_file(config)
	sample_size = 1
	header, sample, delimiter = get_sample(file, sample_size)
	print("Random sample of size", sample_size, "with delimiter", repr(delimiter))
	for row in sample:
		print("Row:", len(row))
		product = dict(zip(header, row))
		product['vendor'] = vendor
		print("product", product.get("MARQUE"), 'fab', product.get("vendor").get("name"))
		handle_product(product, con)
	
def generate_vendor(config: Dict[str, Any], con) -> Dict[str, Any]:
	file_path = config.get("file_path")
	cartouche_path = Path(file_path).with_suffix("") / "B00_CARTOUCHE.csv"
	print(f"Derived cartouche path: {cartouche_path}")
	vendor = None
	if not cartouche_path.exists():
		raise FileNotFoundError(f"B00_CARTOUCHE.csv not found at {cartouche_path}")
	
	# find the 'CARMARQUE' column position in the cartouche file header
	with cartouche_path.open("r", encoding="utf-8", errors="ignore") as cartouche_file:
		header_line = cartouche_file.readline()
		if not header_line:
			raise ValueError("B00_CARTOUCHE.csv is empty; cannot determine vendor name")
		delimiter = detect_delimiter(header_line)
		header_row = next(csv.reader([header_line], delimiter=delimiter))
		header = clean_header(header_row)
		try:
			marque_idx = header.index("CARMARQUE")
		except ValueError:
			raise ValueError("CARMARQUE column not found in B00_CARTOUCHE.csv header; cannot determine vendor name")
		
		try:
			vendor_idx = header.index("FABRICANT")
		except ValueError:
			raise ValueError("FABRICANT column not found in B00_CARTOUCHE.csv header; cannot determine vendor name")
		
		print(f"Found CARMARQUE column at index {marque_idx}, FABRICANT column at index {vendor_idx}")
		for line in cartouche_file:
			row = next(csv.reader([line], delimiter=delimiter))
			if len(row) > marque_idx:
				marque_value = row[marque_idx].strip()
				if marque_value is None:
					raise ValueError("CARMARQUE value is None in B00_CARTOUCHE.csv; cannot determine vendor name")
			else:
				raise ValueError("Row in B00_CARTOUCHE.csv does not have enough columns to access CARMARQUE; cannot determine vendor name")		
		
			if len(row) > vendor_idx:
				vendor_value = row[vendor_idx].strip()
				if vendor_value is None:
					raise ValueError("FABRICANT value is None in B00_CARTOUCHE.csv; cannot determine vendor name")

			print(f"Extracted FABRICANT (vendor)='{vendor_value}', MODELE (brand)='{marque_value}'")
			vendor = vendor if vendor is not None else get_vendor_by_name(vendor_value, con)

	return vendor
			
def get_vendor_by_name(name: str, con) -> Dict[str, Any]:
	with con.cursor() as cur:
		cur.execute("SELECT id, name FROM vendor WHERE name = %s", (name,))
		result = cur.fetchone()
		if result:
			return {"id": result[0], "name": result[1]}
		else:
			print("Vendor not found, inserting new vendor with name:", name)
			cur.execute("INSERT INTO vendor (name) VALUES (%s) RETURNING id", (name,))
			vendor_id = cur.fetchone()[0]
			con.commit()
			return {"id": vendor_id, "name": name}

def get_sample(file, sample_size: int = 100) -> tuple[List[str], List[List[str]]]:
	header_line = file.readline()
	if not header_line:
		raise ValueError("B01_COMMERCE.csv is empty; cannot handle vendor")

	delimiter = detect_delimiter(header_line)
	header_row = next(csv.reader([header_line], delimiter=delimiter))
	header = clean_header(header_row)
	line_count = 0
	sample: List[List[str]] = []
	randint = random.randint
	reader = csv.reader(file, delimiter=delimiter)
	for row in reader:
		line_count += 1
		if line_count <= sample_size:
			sample.append(row)
		else:
			idx = randint(1, line_count)
			if idx <= sample_size:
				sample[idx - 1] = row
	return header, sample, delimiter

def get_file(config: Dict[str, Any]):
	vendor_name = config.get("name") or "unknown"
	vendor_type = config.get("type") or "fabdis"
	file_path = config.get("file_path")
	print(
		f"Handling vendor '{vendor_name}' (type={vendor_type}) file_path={file_path}"
	)
	commerce_path = get_commerce_path(file_path)
	return commerce_path.open("r", encoding="utf-8", errors="ignore")
	

def get_commerce_path(file_path: str) -> Path:
	folder_path = Path(file_path).with_suffix("") if file_path else None
	print(f"Derived folder path: {folder_path}")

	if not folder_path:
		raise ValueError("File path is required in vendor config to determine commerce path")

	commerce_path = folder_path / "B01_COMMERCE.csv"
	if not commerce_path.exists():
		raise FileNotFoundError(f"B01_COMMERCE.csv not found at {commerce_path}")
	return commerce_path
	

def clean_header(row: List[str]) -> List[str]:
	header = [name.strip() for name in row]
	print(f"Cleaned header: {header}")
	return header
    
def get_db_connection():
	db_url = os.getenv("DATABASE_URL")
	if not db_url:
		raise ValueError("DATABASE_URL not set in environment variables")
	return psycopg2.connect(db_url)


def detect_delimiter(header_line: str) -> str:
	for candidate in (";", ",", "\t", "|"):
		if candidate in header_line:
			return candidate
	return ";"


	