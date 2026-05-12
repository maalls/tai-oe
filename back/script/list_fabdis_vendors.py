"""List vendors from config.yml with type 'fabdis'."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("Missing dependency: PyYAML. Install with: pip install PyYAML") from exc


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def iter_fabdis_vendors(config: Dict[str, Any]):
    vendors = (config.get("app") or {}).get("vendor") or {}
    for vendor_name, vendor_cfg in vendors.items():
        if isinstance(vendor_cfg, dict) and vendor_cfg.get("type") == "fabdis":
            yield vendor_name, vendor_cfg


def main() -> None:
    parser = argparse.ArgumentParser(description="List fabdis vendors from config.yml")
    parser.add_argument(
        "--config",
        default="back/config.yml",
        help="Path to config.yml (default: back/config.yml)",
    )

    args = parser.parse_args()
    config = load_config(Path(args.config))

    for vendor_name, vendor_cfg in iter_fabdis_vendors(config):
        file_path = vendor_cfg.get("file_path")
        csv_output_dir = vendor_cfg.get("csv_output_dir")
        print(f"{vendor_name}: file_path={file_path} csv_output_dir={csv_output_dir}")


if __name__ == "__main__":
    main()
