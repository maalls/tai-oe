#!/usr/bin/env python3
"""
CLI tool for querying Qdrant collections.

Usage:
    python src/command/qdrant_cli.py info [--collection NAME]
    python src/command/qdrant_cli.py search "query text" [--limit N] [--collection NAME] [--vendor V] [--part-type T] [--in-stock true|false] [--price-min X] [--price-max X]
    python src/command/qdrant_cli.py list [--limit N] [--offset N] [--collection NAME] [--vendor V] [--part-type T] [--in-stock true|false]
    python src/command/qdrant_cli.py count [--collection NAME] [--vendor V] [--part-type T] [--in-stock true|false]
    python src/command/qdrant_cli.py distinct --field FIELD [--collection NAME] [--limit N]
    python src/command/qdrant_cli.py delete --field FIELD --value VALUE [--collection NAME]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Set

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.qdrant_client_wrapper import VectorDBClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

load_dotenv()

DEFAULT_COLLECTION = "test_commerce_vectors"


def parse_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    value = value.strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true/false for boolean flags")


def build_filters(args) -> Dict:
    filters: Dict = {}
    if args.vendor:
        filters["vendor"] = args.vendor
    if args.part_type:
        filters["part_type"] = args.part_type
    if args.in_stock is not None:
        filters["in_stock"] = args.in_stock
    if getattr(args, "price_min", None) is not None:
        filters["price_min"] = args.price_min
    if getattr(args, "price_max", None) is not None:
        filters["price_max"] = args.price_max
    return filters


def main():
    parser = argparse.ArgumentParser(description="Qdrant CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    info_parser = sub.add_parser("info", help="Show collection info")
    info_parser.add_argument("--collection", default=DEFAULT_COLLECTION)

    search_parser = sub.add_parser("search", help="Semantic search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    search_parser.add_argument("--vendor")
    search_parser.add_argument("--part-type")
    search_parser.add_argument("--in-stock", type=parse_bool)
    search_parser.add_argument("--price-min", type=float)
    search_parser.add_argument("--price-max", type=float)

    list_parser = sub.add_parser("list", help="List parts with optional filters")
    list_parser.add_argument("--limit", type=int, default=50)
    list_parser.add_argument("--offset", type=int, default=0)
    list_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    list_parser.add_argument("--vendor")
    list_parser.add_argument("--part-type")
    list_parser.add_argument("--in-stock", type=parse_bool)

    count_parser = sub.add_parser("count", help="Count parts with optional filters")
    count_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    count_parser.add_argument("--vendor")
    count_parser.add_argument("--part-type")
    count_parser.add_argument("--in-stock", type=parse_bool)

    distinct_parser = sub.add_parser("distinct", help="Count distinct values for a payload field")
    distinct_parser.add_argument("--field", required=True)
    distinct_parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    distinct_parser.add_argument("--limit", type=int, default=0)

    delete_parser = sub.add_parser("delete", help="Delete points matching a payload field value")
    delete_parser.add_argument("--field", required=True)
    delete_parser.add_argument("--value", required=True)
    delete_parser.add_argument("--collection", default=DEFAULT_COLLECTION)

    args = parser.parse_args()

    qdrant_url = os.getenv("QDRANT_URL")
    client = VectorDBClient(url=qdrant_url, collection_name=args.collection)

    if args.command == "info":
        info = client.get_collection_info()
        print(json.dumps(info or {}, indent=2))
        return

    if args.command == "search":
        filters = build_filters(args)
        results = client.query_similar(args.query, filters=filters or None, limit=args.limit)
        print(json.dumps(results, indent=2))
        return

    if args.command == "list":
        filters = build_filters(args)
        results = client.list_parts(limit=args.limit, offset=args.offset, filters=filters or None)
        print(json.dumps(results, indent=2))
        return

    if args.command == "count":
        filters = build_filters(args)
        count = client.count_parts(filters=filters or None)
        print(count)
        return

    if args.command == "distinct":
        field = args.field
        limit = max(args.limit or 0, 0)
        distinct_values: Set[str] = set()
        offset = None

        while True:
            points, offset = client.client.scroll(
                collection_name=args.collection,
                scroll_filter=None,
                limit=200,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not points:
                break

            for point in points:
                payload = point.payload or {}
                value = payload.get(field)
                if value is None:
                    continue
                if isinstance(value, list):
                    for item in value:
                        if item is not None:
                            distinct_values.add(str(item))
                else:
                    distinct_values.add(str(value))

                if limit and len(distinct_values) >= limit:
                    break

            if limit and len(distinct_values) >= limit:
                break

            if offset is None:
                break

        result = {
            "field": field,
            "distinct_count": len(distinct_values),
            "values": sorted(distinct_values) if limit else None,
        }
        print(json.dumps(result, indent=2))
        return

    if args.command == "delete":
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key=args.field,
                    match=MatchValue(value=args.value),
                )
            ]
        )
        result = client.client.delete(
            collection_name=args.collection,
            points_selector=qdrant_filter,
        )
        print(json.dumps({"status": str(result.status)}, indent=2))
        return


if __name__ == "__main__":
    main()
