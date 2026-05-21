from __future__ import annotations

from pathlib import Path


class FabdisImporter:
	def __init__(self, pandas_module: object, supabase_client: object | None):
		self.pd = pandas_module
		self.supabase_client = supabase_client
		self.workbook = None
		self.cartouche_rows = []
		self.commerce_rows = []
		self.imported_cartouche_rows = []
		self.imported_product_rows = []
		self.last_summary = {}
		self._vendor_cache = {}
		self._brand_cache = {}
		self._product_cache = {}
		self._family_cache = {}
		self._product_family_cache = set()
		self.media_rows = []

	def run(self) -> list[dict[str, str | None]]:
		self.load_cartouche()
		self.imported_cartouche_rows = self.import_cartouche()
		self.import_products()
		self.load_media()
		self.import_media()
		return self.imported_cartouche_rows

	def import_products(self) -> list[dict[str, object]]:
		if self.supabase_client is None:
			raise RuntimeError("Supabase client not configured")

		if not self.commerce_rows:
			self.load_commerce()

		self._product_cache = {}
		self._family_cache = {}
		self._product_family_cache = set()

		brand_ids_by_name = self._resolve_brand_ids_for_products()

		imported_rows = []
		product_created_count = 0
		product_updated_count = 0
		family_created_count = 0
		product_family_created_count = 0

		for row in self.commerce_rows:
			brand_id = brand_ids_by_name[row["brand_name"].casefold()]
			product_id, product_created, product_updated = self._ensure_product(row, brand_id)
			if product_created:
				product_created_count += 1
			if product_updated:
				product_updated_count += 1

			family_ids = []
			for family in self._extract_product_families(row):
				family_id, family_created = self._ensure_family(brand_id, family)
				if family_created:
					family_created_count += 1

				_, product_family_created = self._ensure_product_family(product_id, family_id)
				if product_family_created:
					product_family_created_count += 1

				family_ids.append(family_id)

			imported_rows.append(
				{
					**row,
					"brand_id": brand_id,
					"product_id": product_id,
					"family_ids": family_ids,
				}
			)

		self.imported_product_rows = imported_rows
		self.last_summary.update(
			{
				"products_in_file": len(self.commerce_rows),
				"products_created": product_created_count,
				"products_existing": len(self.commerce_rows) - product_created_count,
				"products_updated": product_updated_count,
				"families_created": family_created_count,
				"product_family_created": product_family_created_count,
			}
		)

		return imported_rows

	def import_cartouche(self) -> list[dict[str, str | None]]:
		if self.supabase_client is None:
			raise RuntimeError("Supabase client not configured")

		if not self.cartouche_rows:
			self.load_cartouche()

		self._vendor_cache = {}
		self._brand_cache = {}

		imported_rows = []
		vendor_created_count = 0
		brand_created_count = 0
		vendor_keys = {row["vendor_name"].casefold() for row in self.cartouche_rows}
		brand_keys = {
			(row["vendor_name"].casefold(), row["brand_name"].casefold())
			for row in self.cartouche_rows
		}

		for row in self.cartouche_rows:
			vendor_id, vendor_created = self._ensure_vendor(row["vendor_name"])
			brand_id, brand_created = self._ensure_brand(row, vendor_id)
			if vendor_created:
				vendor_created_count += 1
			if brand_created:
				brand_created_count += 1
			imported_rows.append(
				{
					**row,
					"vendor_id": vendor_id,
					"brand_id": brand_id,
				}
			)

		self.last_summary = {
			"cartouche_rows": len(self.cartouche_rows),
			"vendors_in_file": len(vendor_keys),
			"brands_in_file": len(brand_keys),
			"vendors_created": vendor_created_count,
			"brands_created": brand_created_count,
			"vendors_existing": len(vendor_keys) - vendor_created_count,
			"brands_existing": len(brand_keys) - brand_created_count,
		}

		return imported_rows

	def load(self, fabdis_file: Path) -> None:
		if not fabdis_file.exists():
			raise FileNotFoundError(f"File not found: {fabdis_file}")

		self.workbook = self.pd.ExcelFile(fabdis_file)

	def load_cartouche(self) -> list[dict[str, str | None]]:
		if self.workbook is None:
			raise RuntimeError("Workbook not loaded")

		cartouche_columns = ["FABRICANT", "CARMARQUE", "CARMARQUEURLT", "CAREMAIL"]
		cartouche_df = self.pd.read_excel(
			self.workbook,
			sheet_name="B00_CARTOUCHE",
			usecols=cartouche_columns,
		)
		cartouche_rows = []
		seen_pairs = set()

		for index, row in enumerate(
			cartouche_df.to_dict("records"),
			start=2,
		):
			vendor_name = self._normalize_text(row.get("FABRICANT"))
			brand_name = self._normalize_text(row.get("CARMARQUE"))

			if not vendor_name:
				raise ValueError(
					f"B00_CARTOUCHE row {index}: FABRICANT is required"
				)

			if not brand_name:
				raise ValueError(
					f"B00_CARTOUCHE row {index}: CARMARQUE is required"
				)

			pair_key = (vendor_name.casefold(), brand_name.casefold())
			if pair_key in seen_pairs:
				continue

			seen_pairs.add(pair_key)
			cartouche_rows.append(
				{
					"vendor_name": vendor_name,
					"brand_name": brand_name,
					"brand_website": self._normalize_text(row.get("CARMARQUEURLT")),
					"brand_email": self._normalize_text(row.get("CAREMAIL")),
				}
			)

		self.cartouche_rows = cartouche_rows
		return cartouche_rows

	def load_commerce(self) -> list[dict[str, object]]:
		if self.workbook is None:
			raise RuntimeError("Workbook not loaded")

		commerce_columns = [
			"MARQUE",
			"REFCIALE",
			"LIBELLE40",
			"LIBELLE80",
			"LIBELLE240",
			"TARIF",
			"QT",
			"TVA",
			"FAM1",
			"FAM1L",
			"FAM2",
			"FAM2L",
			"FAM3",
			"FAM3L",
		]
		commerce_df = self.pd.read_excel(
			self.workbook,
			sheet_name="B01_COMMERCE",
			usecols=commerce_columns,
		)
		commerce_rows = []
		seen_products = set()

		for index, row in enumerate(
			commerce_df.to_dict("records"),
			start=2,
		):
			brand_name = self._normalize_text(row.get("MARQUE"))
			sku = self._normalize_text(row.get("REFCIALE"))
			name = (
				self._normalize_text(row.get("LIBELLE80"))
				or self._normalize_text(row.get("LIBELLE40"))
				or self._normalize_text(row.get("LIBELLE240"))
			)

			if not brand_name:
				raise ValueError(f"B01_COMMERCE row {index}: MARQUE is required")

			if not sku:
				raise ValueError(f"B01_COMMERCE row {index}: REFCIALE is required")

			if not name:
				raise ValueError(
					f"B01_COMMERCE row {index}: one of LIBELLE80/LIBELLE40/LIBELLE240 is required"
				)

			tarif = self._normalize_number(row.get("TARIF"))
			qt = self._normalize_number(row.get("QT"))
			if qt is not None and qt <= 0:
				raise ValueError(f"B01_COMMERCE row {index}: QT must be > 0 when provided")

			batch = self._normalize_batch(qt)

			unit_price = tarif
			if tarif is not None and qt not in (None, 0):
				unit_price = tarif / qt

			product_key = (brand_name.casefold(), sku.casefold())
			if product_key in seen_products:
				raise ValueError(
					f"B01_COMMERCE row {index}: duplicate product key MARQUE+REFCIALE ({brand_name}, {sku})"
				)
			seen_products.add(product_key)

			self._validate_family_pair(index, 1, row.get("FAM1"), row.get("FAM1L"))
			self._validate_family_pair(index, 2, row.get("FAM2"), row.get("FAM2L"))
			self._validate_family_pair(index, 3, row.get("FAM3"), row.get("FAM3L"))

			commerce_rows.append(
				{
					"excel_row": index,
					"brand_name": brand_name,
					"sku": sku,
					"name": name,
					"price": unit_price,
					"batch": batch,
					"tax_rate": self._normalize_number(row.get("TVA")),
					"fam1_code": self._normalize_text(row.get("FAM1")),
					"fam1_name": self._normalize_text(row.get("FAM1L")),
					"fam2_code": self._normalize_text(row.get("FAM2")),
					"fam2_name": self._normalize_text(row.get("FAM2L")),
					"fam3_code": self._normalize_text(row.get("FAM3")),
					"fam3_name": self._normalize_text(row.get("FAM3L")),
				}
			)

		self.commerce_rows = commerce_rows
		return commerce_rows

	def load_media(self) -> list[dict[str, object]]:
		if self.workbook is None:
			raise RuntimeError("Workbook not loaded")

		media_columns = ["MARQUE", "REFCIALE", "MTYP", "MNUM", "MURL"]
		media_df = self.pd.read_excel(
			self.workbook,
			sheet_name="B03_MEDIA",
			usecols=media_columns,
		)
		media_rows = []
		for row in media_df.to_dict("records"):
			brand_name = self._normalize_text(row.get("MARQUE"))
			sku = self._normalize_text(row.get("REFCIALE"))
			media_type = self._normalize_text(row.get("MTYP"))
			url = self._normalize_text(row.get("MURL"))

			if not brand_name or not sku or not url:
				continue

			position_raw = self._normalize_number(row.get("MNUM"))
			position = int(round(position_raw)) if position_raw is not None else 0

			media_rows.append(
				{
					"brand_name": brand_name,
					"sku": sku,
					"type": (media_type or "PHOTO").upper(),
					"url": url,
					"position": position,
				}
			)

		self.media_rows = media_rows
		return media_rows

	def import_media(self, return_stats: bool = False) -> dict | None:
		if self.supabase_client is None:
			raise RuntimeError("Supabase client not configured")

		if not self.media_rows:
			self.load_media()

		total_rows = len(self.media_rows)
		print(f"[fabdis:media] Starting media import for {total_rows} row(s)")

		if not self.media_rows:
			print("[fabdis:media] No media rows to process")
			self.last_summary["media_upserted"] = 0
			self.last_summary["media_existing"] = 0
			self.last_summary["media_skipped"] = 0
			if return_stats:
				return {"created": 0, "existing": 0, "skipped": 0}
			return None

		skipped = 0
		upserted = 0
		existing = 0

		# 1) Resolve brand ids once per distinct brand name.
		def _is_uri_too_long_error(exc: Exception) -> bool:
			msg = str(exc).lower()
			return "uri too long" in msg or "'code': 414" in msg or '"code": 414' in msg

		brand_ids_by_name: dict[str, str] = {}
		for row in self.media_rows:
			brand_name = row["brand_name"]
			brand_key = brand_name.casefold()
			if brand_key in brand_ids_by_name:
				continue

			brand_id = next(
				(v for (_, bname), v in self._brand_cache.items() if bname == brand_key),
				None,
			)
			if not brand_id:
				resp = (
					self.supabase_client.table("brand")
					.select("id")
					.ilike("name", brand_name)
					.limit(1)
					.execute()
				)
				if resp.data:
					brand_id = resp.data[0]["id"]

			if brand_id:
				brand_ids_by_name[brand_key] = brand_id
		print(
			f"[fabdis:media] Resolved {len(brand_ids_by_name)} distinct brand(s) from {len({r['brand_name'].casefold() for r in self.media_rows})} in file"
		)

		# 2) Resolve product ids once per distinct (brand_id, sku).
		product_ids_by_key: dict[tuple[str, str], str] = {}
		sku_by_brand_id: dict[str, set[str]] = {}
		for row in self.media_rows:
			brand_key = row["brand_name"].casefold()
			brand_id = brand_ids_by_name.get(brand_key)
			if not brand_id:
				continue
			sku_by_brand_id.setdefault(brand_id, set()).add(row["sku"])

		product_lookup_chunk_size = 500
		total_lookup_pairs = sum(len(skus) for skus in sku_by_brand_id.values())
		print(
			f"[fabdis:media] Looking up {total_lookup_pairs} distinct (brand, sku) pair(s)"
		)

		for brand_id, sku_set in sku_by_brand_id.items():
			skus = sorted(sku_set)
			total_brand_chunks = (len(skus) + product_lookup_chunk_size - 1) // product_lookup_chunk_size
			for idx in range(0, len(skus), product_lookup_chunk_size):
				initial_chunk = skus[idx : idx + product_lookup_chunk_size]
				chunk_no = (idx // product_lookup_chunk_size) + 1
				pending_chunks: list[list[str]] = [initial_chunk]

				while pending_chunks:
					sku_chunk = pending_chunks.pop(0)
					try:
						resp = (
							self.supabase_client.table("product")
							.select("id,sku")
							.eq("brand_id", brand_id)
							.in_("sku", sku_chunk)
							.execute()
						)
					except Exception as exc:
						if _is_uri_too_long_error(exc) and len(sku_chunk) > 1:
							mid = len(sku_chunk) // 2
							left = sku_chunk[:mid]
							right = sku_chunk[mid:]
							print(
								f"[fabdis:media] Product lookup chunk too large ({len(sku_chunk)} sku(s)); splitting into {len(left)} + {len(right)}"
							)
							pending_chunks.insert(0, right)
							pending_chunks.insert(0, left)
							continue
						raise

					print(
						f"[fabdis:media] Product lookup brand {brand_id} chunk {chunk_no}/{total_brand_chunks}: {len(sku_chunk)} sku(s)"
					)
					for item in resp.data or []:
						product_id = item.get("id")
						sku = item.get("sku")
						if not product_id or not sku:
							continue
						product_key = (brand_id, str(sku))
						product_ids_by_key[product_key] = product_id
						self._product_cache[product_key] = product_id
		print(
			f"[fabdis:media] Resolved {len(product_ids_by_key)} product(s) for media rows"
		)

		# 3) Build candidate rows and skip unresolved products.
		candidate_rows = []
		for row in self.media_rows:
			brand_id = brand_ids_by_name.get(row["brand_name"].casefold())
			if not brand_id:
				skipped += 1
				continue

			product_key = (brand_id, row["sku"])
			product_id = product_ids_by_key.get(product_key)
			if not product_id:
				skipped += 1
				continue

			candidate_rows.append((row, product_id))
		print(
			f"[fabdis:media] Candidate media rows: {len(candidate_rows)} (ignored missing product/brand: {skipped})"
		)

		if not candidate_rows:
			print("[fabdis:media] Nothing to upsert after filtering")
			self.last_summary["media_upserted"] = 0
			self.last_summary["media_existing"] = 0
			self.last_summary["media_skipped"] = skipped
			if return_stats:
				return {"created": 0, "existing": 0, "skipped": skipped}
			return None

		# 4) Prefetch existing media keys in chunks to avoid per-row existence checks.
		existing_keys: set[tuple[str, str, str]] = set()
		product_ids = sorted({product_id for _, product_id in candidate_rows})
		chunk_size = 200
		total_prefetch_chunks = (len(product_ids) + chunk_size - 1) // chunk_size
		print(
			f"[fabdis:media] Prefetching existing media for {len(product_ids)} product(s) in {total_prefetch_chunks} chunk(s)"
		)
		for idx in range(0, len(product_ids), chunk_size):
			chunk = product_ids[idx : idx + chunk_size]
			chunk_no = (idx // chunk_size) + 1
			pending_chunks: list[list[str]] = [chunk]
			while pending_chunks:
				prefetch_chunk = pending_chunks.pop(0)
				try:
					resp = (
						self.supabase_client.table("product_media")
						.select("product_id,type,url")
						.in_("product_id", prefetch_chunk)
						.execute()
					)
				except Exception as exc:
					if _is_uri_too_long_error(exc) and len(prefetch_chunk) > 1:
						mid = len(prefetch_chunk) // 2
						left = prefetch_chunk[:mid]
						right = prefetch_chunk[mid:]
						print(
							f"[fabdis:media] Prefetch chunk too large ({len(prefetch_chunk)} product(s)); splitting into {len(left)} + {len(right)}"
						)
						pending_chunks.insert(0, right)
						pending_chunks.insert(0, left)
						continue
					raise

				print(
					f"[fabdis:media] Prefetch chunk {chunk_no}/{total_prefetch_chunks}: {len(prefetch_chunk)} product(s)"
				)
				for item in resp.data or []:
					pid = item.get("product_id")
					mtype = item.get("type")
					url = item.get("url")
					if pid and mtype and url:
						existing_keys.add((pid, str(mtype), str(url)))

		# 5) Count existing and batch upsert only new media entries.
		rows_to_upsert = []
		for row, product_id in candidate_rows:
			media_key = (product_id, row["type"], row["url"])
			if media_key in existing_keys:
				existing += 1
				continue

			rows_to_upsert.append(
				{
					"product_id": product_id,
					"url": row["url"],
					"type": row["type"],
					"source": "fabdis",
					"position": row["position"],
				}
			)
		print(
			f"[fabdis:media] Existing media: {existing}, to create: {len(rows_to_upsert)}"
		)

		total_upsert_chunks = (len(rows_to_upsert) + chunk_size - 1) // chunk_size
		for idx in range(0, len(rows_to_upsert), chunk_size):
			chunk = rows_to_upsert[idx : idx + chunk_size]
			chunk_no = (idx // chunk_size) + 1
			result = (
				self.supabase_client.table("product_media")
				.upsert(chunk, on_conflict="product_id,type,url")
				.execute()
			)
			if getattr(result, "error", None):
				raise RuntimeError(f"Failed to upsert media batch: {result.error}")
			upserted += len(chunk)
			print(
				f"[fabdis:media] Upsert chunk {chunk_no}/{total_upsert_chunks}: +{len(chunk)} (total created: {upserted})"
			)

		print(
			f"[fabdis:media] Done. created={upserted}, existing={existing}, ignored={skipped}"
		)

		self.last_summary["media_upserted"] = upserted
		self.last_summary["media_existing"] = existing
		self.last_summary["media_skipped"] = skipped
		if return_stats:
			return {"created": upserted, "existing": existing, "skipped": skipped}
		return None

	def print_sheet_names(self) -> None:
		for sheet_name in self.workbook.sheet_names:
			print(sheet_name)

	def _ensure_vendor(self, vendor_name: str) -> tuple[str, bool]:
		vendor_key = vendor_name.casefold()
		cached_vendor_id = self._vendor_cache.get(vendor_key)
		if cached_vendor_id:
			return cached_vendor_id, False

		response = (
			self.supabase_client.table("vendor")
			.select("id")
			.eq("name", vendor_name)
			.limit(1)
			.execute()
		)

		if getattr(response, "error", None):
			raise RuntimeError(f"Failed to query vendor '{vendor_name}': {response.error}")

		if response.data:
			vendor_id = response.data[0].get("id")
			if not vendor_id:
				raise RuntimeError(f"Vendor '{vendor_name}' returned without id")
			self._vendor_cache[vendor_key] = vendor_id
			return vendor_id, False

		created = self.supabase_client.table("vendor").insert({"name": vendor_name}).execute()
		if getattr(created, "error", None):
			raise RuntimeError(f"Failed to create vendor '{vendor_name}': {created.error}")

		if not created.data or not created.data[0].get("id"):
			raise RuntimeError(f"Vendor '{vendor_name}' insert returned no id")

		vendor_id = created.data[0]["id"]
		self._vendor_cache[vendor_key] = vendor_id
		return vendor_id, True

	def _ensure_brand(self, row: dict[str, str | None], vendor_id: str) -> tuple[str, bool]:
		brand_name = row["brand_name"]
		brand_key = (vendor_id, brand_name.casefold())
		cached_brand_id = self._brand_cache.get(brand_key)
		if cached_brand_id:
			return cached_brand_id, False

		response = (
			self.supabase_client.table("brand")
			.select("id")
			.eq("vendor_id", vendor_id)
			.eq("name", brand_name)
			.limit(1)
			.execute()
		)

		if getattr(response, "error", None):
			raise RuntimeError(
				f"Failed to query brand '{brand_name}' for vendor '{row['vendor_name']}': {response.error}"
			)

		if response.data:
			brand_id = response.data[0].get("id")
			if not brand_id:
				raise RuntimeError(
					f"Brand '{brand_name}' for vendor '{row['vendor_name']}' returned without id"
				)
			self._brand_cache[brand_key] = brand_id
			return brand_id, False

		insert_data = {
			"name": brand_name,
			"marque": brand_name,
			"vendor_id": vendor_id,
			"website": row["brand_website"],
			"email": row["brand_email"],
		}
		created = self.supabase_client.table("brand").insert(insert_data).execute()
		if getattr(created, "error", None):
			raise RuntimeError(
				f"Failed to create brand '{brand_name}' for vendor '{row['vendor_name']}': {created.error}"
			)

		if not created.data or not created.data[0].get("id"):
			raise RuntimeError(
				f"Brand '{brand_name}' for vendor '{row['vendor_name']}' insert returned no id"
			)

		brand_id = created.data[0]["id"]
		self._brand_cache[brand_key] = brand_id
		return brand_id, True

	def _resolve_brand_ids_for_products(self) -> dict[str, str]:
		brand_ids = {}
		for brand_name in {row["brand_name"] for row in self.commerce_rows}:
			response = (
				self.supabase_client.table("brand")
				.select("id")
				.eq("name", brand_name)
				.execute()
			)

			if getattr(response, "error", None):
				raise RuntimeError(f"Failed to query brand '{brand_name}': {response.error}")

			if not response.data:
				raise ValueError(f"No brand found for product MARQUE '{brand_name}'")

			if len(response.data) > 1:
				raise ValueError(
					f"Ambiguous brand for product MARQUE '{brand_name}': {len(response.data)} rows"
				)

			brand_id = response.data[0].get("id")
			if not brand_id:
				raise RuntimeError(f"Brand '{brand_name}' returned without id")

			brand_ids[brand_name.casefold()] = brand_id

		return brand_ids

	def _extract_product_families(self, row: dict[str, object]) -> list[dict[str, str]]:
		families = []

		for level in (1, 2, 3):
			code = row[f"fam{level}_code"]
			name = row[f"fam{level}_name"]
			if not code and not name:
				continue

			families.append(
				{
					"type": None,
					"code": code,
					"name": name,
				}
			)

		return families

	def _ensure_product(self, row: dict[str, object], brand_id: str) -> tuple[str, bool, bool]:
		product_key = (brand_id, row["sku"])
		cached_product_id = self._product_cache.get(product_key)
		if cached_product_id:
			return cached_product_id, False, False

		response = (
			self.supabase_client.table("product")
			.select("id,price,batch")
			.eq("brand_id", brand_id)
			.eq("sku", row["sku"])
			.limit(1)
			.execute()
		)

		if getattr(response, "error", None):
			raise RuntimeError(
				f"Failed to query product '{row['sku']}' for brand '{row['brand_name']}': {response.error}"
			)

		if response.data:
			product_id = response.data[0].get("id")
			if not product_id:
				raise RuntimeError(
					f"Product '{row['sku']}' for brand '{row['brand_name']}' returned without id"
				)

			product_updated = False
			new_price = row["price"]
			new_batch = row["batch"]
			existing_price = response.data[0].get("price")
			existing_batch = response.data[0].get("batch")
			updates = {}
			if self._numbers_different(existing_price, new_price):
				updates["price"] = new_price
			if existing_batch != new_batch:
				updates["batch"] = new_batch

			if updates:
				updated = (
					self.supabase_client.table("product")
					.update(updates)
					.eq("id", product_id)
					.execute()
				)
				if getattr(updated, "error", None):
					raise RuntimeError(
						f"Failed to update product '{row['sku']}' (id={product_id}): {updated.error}"
					)
				product_updated = True

			self._product_cache[product_key] = product_id
			return product_id, False, product_updated

		insert_data = {
			"brand_id": brand_id,
			"sku": row["sku"],
			"name": row["name"],
		}

		if row["price"] is not None:
			insert_data["price"] = row["price"]

		if row["batch"] is not None:
			insert_data["batch"] = row["batch"]

		if row["tax_rate"] is not None:
			insert_data["default_tax_rate"] = row["tax_rate"]

		created = self.supabase_client.table("product").insert(insert_data).execute()
		if getattr(created, "error", None):
			raise RuntimeError(
				f"Failed to create product '{row['sku']}' for brand '{row['brand_name']}': {created.error}"
			)

		if not created.data or not created.data[0].get("id"):
			raise RuntimeError(
				f"Product '{row['sku']}' for brand '{row['brand_name']}' insert returned no id"
			)

		product_id = created.data[0]["id"]
		self._product_cache[product_key] = product_id
		return product_id, True, False

	def _ensure_family(self, brand_id: str, family: dict[str, str]) -> tuple[str, bool]:
		family_key = (brand_id, family["code"])
		cached_family_id = self._family_cache.get(family_key)
		if cached_family_id:
			return cached_family_id, False

		query = (
			self.supabase_client.table("family")
			.select("id,type")
			.eq("brand_id", brand_id)
			.eq("code", family["code"])
		)
		response = query.limit(1).execute()

		if getattr(response, "error", None):
			raise RuntimeError(
				f"Failed to query family '{family['type']}:{family['code']}': {response.error}"
			)

		if response.data:
			family_id = response.data[0].get("id")
			if not family_id:
				raise RuntimeError(
					f"Family '{family['type']}:{family['code']}' returned without id"
				)
			self._family_cache[family_key] = family_id
			return family_id, False

		insert_data = {
			"brand_id": brand_id,
			"type": None,
			"code": family["code"],
			"name": family["name"],
		}
		created = self.supabase_client.table("family").insert(insert_data).execute()
		if getattr(created, "error", None):
			raise RuntimeError(
				f"Failed to create family '{family['type']}:{family['code']}': {created.error}"
			)

		if not created.data or not created.data[0].get("id"):
			raise RuntimeError(
				f"Family '{family['type']}:{family['code']}' insert returned no id"
			)

		family_id = created.data[0]["id"]
		self._family_cache[family_key] = family_id
		return family_id, True

	def _ensure_product_family(self, product_id: str, family_id: str) -> tuple[str, bool]:
		pair = (product_id, family_id)
		if pair in self._product_family_cache:
			return f"{product_id}:{family_id}", False

		response = (
			self.supabase_client.table("product_family")
			.select("product_id")
			.eq("product_id", product_id)
			.eq("family_id", family_id)
			.limit(1)
			.execute()
		)

		if getattr(response, "error", None):
			raise RuntimeError(
				f"Failed to query product_family '{product_id}->{family_id}': {response.error}"
			)

		if response.data:
			self._product_family_cache.add(pair)
			return f"{product_id}:{family_id}", False

		created = (
			self.supabase_client.table("product_family")
			.insert({"product_id": product_id, "family_id": family_id})
			.execute()
		)
		if getattr(created, "error", None):
			raise RuntimeError(
				f"Failed to create product_family '{product_id}->{family_id}': {created.error}"
			)

		self._product_family_cache.add(pair)
		return f"{product_id}:{family_id}", True

	def _normalize_text(self, value: object) -> str | None:
		if value is None:
			return None

		if self.pd.isna(value):
			return None

		text = str(value).strip()
		if not text:
			return None

		return text

	def _normalize_number(self, value: object) -> float | None:
		if value is None:
			return None

		if self.pd.isna(value):
			return None

		if isinstance(value, str):
			text = value.strip().replace(",", ".")
			if not text:
				return None
			return float(text)

		return float(value)

	def _normalize_batch(self, value: object) -> int | None:
		if value is None:
			return None

		if self.pd.isna(value):
			return None

		batch_value = self._normalize_number(value)
		if batch_value is None:
			return None

		if abs(batch_value - round(batch_value)) > 1e-9:
			raise ValueError(f"QT must be an integer value, got {value!r}")

		return int(round(batch_value))

	def _numbers_different(self, current: object, new_value: object) -> bool:
		current_number = self._normalize_number(current)
		new_number = self._normalize_number(new_value)

		if current_number is None and new_number is None:
			return False

		if current_number is None or new_number is None:
			return True

		return abs(current_number - new_number) > 1e-9

	def _validate_family_pair(self, row_index: int, level: int, code_value: object, name_value: object) -> None:
		code = self._normalize_text(code_value)
		name = self._normalize_text(name_value)

		if code and not name:
			raise ValueError(
				f"B01_COMMERCE row {row_index}: FAM{level}L is required when FAM{level} is set"
			)

		if name and not code:
			raise ValueError(
				f"B01_COMMERCE row {row_index}: FAM{level} is required when FAM{level}L is set"
			)
