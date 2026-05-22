"""Fabdis vendor handler."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Tuple
from src.infrastructure.runtime.env_loader import load_runtime_env
from vendor import handle_vendor

load_runtime_env(current_file=__file__)

try:
	import yaml
except ImportError as exc:  # pragma: no cover
	raise ImportError("Missing dependency: PyYAML. Install with: pip install PyYAML") from exc


def load_config(config_path: Path) -> Dict[str, Any]:
	if not config_path.exists():
		raise FileNotFoundError(f"Config not found: {config_path}")
	with config_path.open("r", encoding="utf-8") as file:
		return yaml.safe_load(file) or {}


def iter_fabdis_vendors_config(config: Dict[str, Any]) -> Iterator[Tuple[str, Dict[str, Any]]]:
	vendors = (config.get("app") or {}).get("vendor") or {}
	for vendor_name, vendor_cfg in vendors.items():
		if isinstance(vendor_cfg, dict) and vendor_cfg.get("type") == "fabdis":
			vendor_cfg = {**vendor_cfg, "name": vendor_name}
			yield vendor_name, vendor_cfg


def main() -> None:
	config_path = Path(__file__).resolve().parents[3] / "config.yml"
	config = load_config(config_path)
	vendors = (config.get("app") or {}).get("vendor") or {}
	print(f"Loaded config: {config_path}")
	print(f"Vendors found: {', '.join(vendors.keys()) if vendors else 'none'}")
	found = False
	for _, vendor_cfg in iter_fabdis_vendors_config(config):
		found = True
		handle_vendor(vendor_cfg)
	if not found:
		print("No vendors with type 'fabdis' found in config.yml")


if __name__ == "__main__":
	main()
